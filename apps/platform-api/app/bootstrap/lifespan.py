from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from app.config import Settings
from app.db.access import count_super_admins, create_user_account, get_user_by_username
from app.db.init_db import create_core_tables
from app.db.session import build_engine, build_session_factory, session_scope
from app.security.password import hash_password
from fastapi import FastAPI

logger = logging.getLogger("proxy")


def _ensure_bootstrap_admin(app: FastAPI, settings: Settings) -> None:
    session_factory = app.state.db_session_factory
    with session_scope(session_factory) as session:
        bootstrap_user = get_user_by_username(
            session, settings.bootstrap_admin_username
        )
        if bootstrap_user is None:
            if count_super_admins(session) > 0:
                return
            create_user_account(
                session,
                username=settings.bootstrap_admin_username,
                password_hash=hash_password(settings.bootstrap_admin_password),
                is_super_admin=True,
            )
            logger.warning(
                "bootstrap_admin_created username=%s", settings.bootstrap_admin_username
            )
            return

        changed = False
        if bootstrap_user.status != "active":
            bootstrap_user.status = "active"
            changed = True
        if not bootstrap_user.is_super_admin:
            bootstrap_user.is_super_admin = True
            changed = True
        if not bootstrap_user.password_hash:
            bootstrap_user.password_hash = hash_password(
                settings.bootstrap_admin_password
            )
            changed = True
        if changed:
            session.flush()
            logger.warning(
                "bootstrap_admin_reconciled username=%s",
                settings.bootstrap_admin_username,
            )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings

    timeout = httpx.Timeout(
        connect=5.0,
        read=settings.proxy_timeout_seconds,
        write=settings.proxy_timeout_seconds,
        pool=5.0,
    )
    app.state.client = httpx.AsyncClient(timeout=timeout)

    if settings.platform_db_enabled:
        app.state.db_engine = build_engine(settings)
        app.state.db_session_factory = build_session_factory(app.state.db_engine)
        if settings.platform_db_auto_create:
            create_core_tables(app.state.db_engine)
        _ensure_bootstrap_admin(app, settings)
        logger.info(
            "startup_platform_db_enabled auto_create=%s",
            settings.platform_db_auto_create,
        )
    else:
        logger.info("startup_platform_db_disabled")

    try:
        yield
    finally:
        if settings.platform_db_enabled:
            app.state.db_engine.dispose()
        await app.state.client.aclose()
        logger.info("shutdown_complete")
