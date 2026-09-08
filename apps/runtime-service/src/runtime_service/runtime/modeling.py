"""Explicit Provider-to-ChatModel construction for resolved Runtime config."""

from __future__ import annotations

import os
from collections.abc import Mapping

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

from runtime_service.runtime.contracts import ResolvedRuntimeConfig
from runtime_service.runtime.errors import RuntimeResolutionError


def _generation_kwargs(config: ResolvedRuntimeConfig) -> dict[str, object]:
    return {
        key: value
        for key, value in {
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
        }.items()
        if value is not None
    }


def _required(settings: Mapping[str, str], name: str) -> str:
    value = settings.get(name)
    if not value:
        raise RuntimeResolutionError("runtime.model.initialization_failed", "model_id")
    return value


def build_model(
    config: ResolvedRuntimeConfig,
    *,
    env: Mapping[str, str] | None = None,
    connection: Mapping[str, str] | None = None,
) -> BaseChatModel:
    """Build a model from a resolved ID; never accepts raw request config."""

    if not isinstance(config, ResolvedRuntimeConfig):
        raise RuntimeResolutionError("runtime.model.invalid_config")
    settings = os.environ if env is None else env
    provider, separator, model_name = config.model_id.partition(":")
    model_name = model_name if separator else config.model_id
    protocol = ""

    if connection is not None:
        provider = str(connection.get("provider", provider)).strip().lower()
        model_name = connection.get("model", model_name)
        protocol = str(connection.get("protocol", "")).strip().lower()

    kwargs = _generation_kwargs(config)

    try:
        conn_api_key = connection.get("api_key") if connection is not None else None
        conn_base_url = connection.get("base_url") if connection is not None else None

        if provider in ("deepseek", "deepseek-proxy") or protocol == "deepseek":
            return ChatDeepSeek(
                model=model_name,
                api_key=conn_api_key or _required(settings, "DEEPSEEK_PROXY_API_KEY"),
                base_url=conn_base_url or _required(settings, "DEEPSEEK_PROXY_URL"),
                **kwargs,
            )
        if provider in ("openai", "gpt-proxy") or protocol in ("openai", "openai-compatible", "openai_compatible"):
            return ChatOpenAI(
                model=model_name,
                api_key=conn_api_key or settings.get("GPT_PROXY_API_KEY") or "EMPTY",
                base_url=conn_base_url or _required(settings, "GPT_PROXY_URL"),
                **kwargs,
            )
        if connection is not None and conn_base_url:
            return ChatOpenAI(
                model=model_name,
                api_key=conn_api_key or "EMPTY",
                base_url=conn_base_url,
                **kwargs,
            )
        return init_chat_model(config.model_id, **kwargs)
    except RuntimeResolutionError:
        raise
    except Exception as exc:
        raise RuntimeResolutionError("runtime.model.initialization_failed", "model_id") from exc


__all__ = ["build_model"]
