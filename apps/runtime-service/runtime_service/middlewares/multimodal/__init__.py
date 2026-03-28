# pyright: reportMissingImports=false, reportMissingModuleSource=false
from __future__ import annotations

from runtime_service.middlewares.multimodal.middleware import (
    MultimodalMiddleware,
)
from runtime_service.middlewares.multimodal.parsing import (
    _extract_openai_response_text,
    _extract_pdf_text,
    _parse_model_response,
    _resolve_parser_transport,
)
from runtime_service.middlewares.multimodal.prompting import (
    build_multimodal_summary,
    build_multimodal_system_message,
)
from runtime_service.middlewares.multimodal.protocol import (
    build_attachment_artifact,
    collect_attachment_artifacts,
    collect_current_turn_attachment_artifacts,
    get_latest_human_message_with_attachments,
    normalize_message_content,
    normalize_messages,
)
from runtime_service.middlewares.multimodal.types import (
    AttachmentArtifact,
    AttachmentKind,
    AttachmentStatus,
    DEFAULT_MULTIMODAL_MODEL_ID,
    MULTIMODAL_ATTACHMENTS_KEY,
    MULTIMODAL_SUMMARY_KEY,
    MultimodalAgentState,
    ParserResult,
)
from runtime_service.runtime.modeling import resolve_model_by_id

__all__ = [
    "AttachmentArtifact",
    "AttachmentKind",
    "AttachmentStatus",
    "MULTIMODAL_ATTACHMENTS_KEY",
    "MULTIMODAL_SUMMARY_KEY",
    "DEFAULT_MULTIMODAL_MODEL_ID",
    "MultimodalAgentState",
    "MultimodalMiddleware",
    "ParserResult",
    "build_attachment_artifact",
    "build_multimodal_summary",
    "build_multimodal_system_message",
    "collect_attachment_artifacts",
    "collect_current_turn_attachment_artifacts",
    "get_latest_human_message_with_attachments",
    "normalize_message_content",
    "normalize_messages",
    "_extract_openai_response_text",
    "_extract_pdf_text",
    "_parse_model_response",
    "_resolve_parser_transport",
    "resolve_model_by_id",
]
