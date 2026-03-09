from __future__ import annotations

from app.db.access import (
    create_refresh_token,
    get_refresh_token,
    get_user_by_id,
    get_user_by_username,
    parse_uuid,
    revoke_all_refresh_tokens_for_user,
    revoke_refresh_token,
    update_user_password_hash,
)
from app.db.session import session_scope
from app.security.password import hash_password, verify_password
from app.security.token import InvalidTokenError, create_access_token
from app.security.token import create_refresh_token as sign_refresh_token
from app.security.token import decode_refresh_token
from fastapi import APIRouter, HTTPException, Request

from .common import current_user_id_from_request, require_db_session_factory
from .schemas import ChangePasswordRequest, LoginRequest, LogoutRequest, RefreshRequest

router = APIRouter(prefix="/auth", tags=["management-auth"])


@router.post("/login")
async def login(request: Request, payload: LoginRequest):
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        user = get_user_by_username(session, payload.username)
        if (
            user is None
            or user.status != "active"
            or not verify_password(payload.password, user.password_hash)
        ):
            raise HTTPException(status_code=401, detail="invalid_credentials")

        access_token = create_access_token(
            user_id=str(user.id),
            username=user.username,
            settings=request.app.state.settings,
        )
        refresh_token, token_id = sign_refresh_token(
            user_id=str(user.id),
            username=user.username,
            settings=request.app.state.settings,
        )
        create_refresh_token(
            session,
            user_id=user.id,
            token_id=token_id,
            ttl_seconds=request.app.state.settings.jwt_refresh_ttl_seconds,
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "is_super_admin": bool(user.is_super_admin),
            },
        }


@router.post("/refresh")
async def refresh_token(request: Request, payload: RefreshRequest):
    session_factory = require_db_session_factory(request)
    try:
        decoded = decode_refresh_token(
            payload.refresh_token, request.app.state.settings
        )
    except InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="invalid_refresh_token") from exc
    token_id = str(decoded.get("jti") or "")
    user_id = parse_uuid(str(decoded.get("sub") or ""))
    username = str(decoded.get("username") or "")
    if not token_id or user_id is None or not username:
        raise HTTPException(status_code=401, detail="invalid_refresh_token")

    with session_scope(session_factory) as session:
        token_row = get_refresh_token(session, token_id)
        if token_row is None or token_row.revoked_at is not None:
            raise HTTPException(status_code=401, detail="refresh_token_revoked")
        user = get_user_by_id(session, user_id)
        if user is None or user.status != "active":
            raise HTTPException(status_code=401, detail="user_not_active")

        revoke_refresh_token(session, token_id)
        new_refresh, new_token_id = sign_refresh_token(
            user_id=str(user.id),
            username=user.username,
            settings=request.app.state.settings,
        )
        create_refresh_token(
            session,
            user_id=user.id,
            token_id=new_token_id,
            ttl_seconds=request.app.state.settings.jwt_refresh_ttl_seconds,
        )
        access_token = create_access_token(
            user_id=str(user.id),
            username=user.username,
            settings=request.app.state.settings,
        )
        return {
            "access_token": access_token,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }


@router.post("/logout")
async def logout(request: Request, payload: LogoutRequest):
    session_factory = require_db_session_factory(request)
    try:
        decoded = decode_refresh_token(
            payload.refresh_token, request.app.state.settings
        )
    except InvalidTokenError as exc:
        raise HTTPException(status_code=400, detail="invalid_refresh_token") from exc
    token_id = str(decoded.get("jti") or "")
    if not token_id:
        raise HTTPException(status_code=400, detail="invalid_refresh_token")

    with session_scope(session_factory) as session:
        revoke_refresh_token(session, token_id)
    return {"ok": True}


@router.post("/change-password")
async def change_password(request: Request, payload: ChangePasswordRequest):
    user_id = current_user_id_from_request(request)
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        user = get_user_by_id(session, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="user_not_found")
        if not verify_password(payload.old_password, user.password_hash):
            raise HTTPException(status_code=401, detail="invalid_credentials")
        update_user_password_hash(session, user, hash_password(payload.new_password))
        revoke_all_refresh_tokens_for_user(session, user.id)
    return {"ok": True}
