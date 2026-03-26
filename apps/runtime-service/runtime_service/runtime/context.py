from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any


@dataclass
class RuntimeContext:
    # ==================== Deployment / Tenant Context ====================
    # These identity fields should come from trusted auth, not client input.
    user_id: str | None = None
    tenant_id: str | None = None
    role: str | None = None
    permissions: list[str] | None = None

    # ==================== Runtime Feature Parameters ====================
    environment: str | None = None
    model_id: str | None = None
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    enable_tools: bool | None = None
    tools: list[str] | None = None
    skills: list[str] | None = None
    subagents: list[dict[str, object]] | None = None

    def to_mapping(self) -> dict[str, Any]:
        # Drop None values so downstream resolver can use fallback logic clearly.
        data = dataclasses.asdict(self)
        return {key: value for key, value in data.items() if value is not None}
