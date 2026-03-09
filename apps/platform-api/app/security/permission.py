from __future__ import annotations

from fastapi import HTTPException

ROLE_ORDER = {
    "executor": 1,
    "editor": 2,
    "admin": 3,
}


def assert_role_at_least(current_role: str | None, required_role: str) -> None:
    current_value = ROLE_ORDER.get(current_role or "", 0)
    required_value = ROLE_ORDER.get(required_role, 0)
    if current_value < required_value:
        raise HTTPException(status_code=403, detail="insufficient_project_role")


def assert_role_in_allowed_set(
    current_role: str | None, allowed_roles: set[str]
) -> None:
    if current_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="insufficient_project_role")
