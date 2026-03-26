from __future__ import annotations

from functools import lru_cache
from typing import Any

from runtime_service.conf.settings import require_model_spec
from runtime_service.runtime.options import AppRuntimeConfig, ModelSpec
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel


def _init_chat_model(
    *,
    model_provider: str,
    model: str,
    api_key: str,
    base_url: str | None = None,
) -> BaseChatModel:
    kwargs: dict[str, Any] = {
        "api_key": api_key,
    }
    if base_url:
        kwargs["base_url"] = base_url

    return init_chat_model(model=model, model_provider=model_provider, **kwargs)


def resolve_model(model_spec: ModelSpec) -> BaseChatModel:
    provider = model_spec.model_provider.strip()
    model = model_spec.model.strip()
    key = model_spec.api_key.strip()
    if not provider:
        raise ValueError("Missing model_provider.")
    if not model:
        raise ValueError("Missing model_name.")
    if not key:
        raise ValueError("Missing model_api_key.")

    normalized_base_url = (
        model_spec.base_url.strip() if isinstance(model_spec.base_url, str) else None
    )
    normalized_base_url = normalized_base_url or None

    return _init_chat_model(
        model_provider=provider,
        model=model,
        api_key=key,
        base_url=normalized_base_url,
    )


@lru_cache(maxsize=16)
def resolve_model_by_id(model_id: str) -> BaseChatModel:
    resolved_id, model_spec = require_model_spec(model_id)
    del resolved_id
    return _init_chat_model(
        model_provider=model_spec["model_provider"],
        model=model_spec["model"],
        api_key=model_spec["api_key"],
        base_url=model_spec["base_url"],
    )


def apply_model_runtime_params(model: Any, options: AppRuntimeConfig) -> Any:
    kwargs: dict[str, Any] = {}
    if options.temperature is not None:
        kwargs["temperature"] = options.temperature
    if options.max_tokens is not None:
        kwargs["max_tokens"] = options.max_tokens
    if options.top_p is not None:
        kwargs["top_p"] = options.top_p
    if not kwargs:
        return model
    return model.bind(**kwargs)
