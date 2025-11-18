"""
Agentic RAG 配置文件
整合来自 sematic_study.py 和 file_rag/core/config.py 的配置
"""

import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """RAG系统配置类"""

    # API配置
    API_V1_STR: str = "/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")

    # CORS设置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # LLM配置 - 基于 sematic_study.py 的配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "8192"))

    # 向量数据库配置 - 基于 sematic_study.py 的配置
    MILVUS_URI: str = os.getenv("MILVUS_URI", "http://localhost:19530")

    # 嵌入模型配置 - 基于 sematic_study.py 的配置
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL", "http://localhost:11434")
    EMBEDDING_TEMPERATURE: float = float(os.getenv("EMBEDDING_TEMPERATURE", "0.0"))

    # 图像解析配置 - 基于 sematic_study.py 的配置
    IMAGE_PARSER_API_BASE: str = os.getenv(
        "IMAGE_PARSER_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"
    )
    IMAGE_PARSER_API_KEY: str = os.getenv("IMAGE_PARSER_API_KEY", "")
    IMAGE_PARSER_MODEL: str = os.getenv(
        "IMAGE_PARSER_MODEL", "doubao-seed-1-6-vision-250815"
    )
    IMAGE_PARSER_MAX_TOKENS: int = int(os.getenv("IMAGE_PARSER_MAX_TOKENS", "8192"))

    # 图像解析提示词 - 基于 sematic_study.py 的配置
    IMAGE_PARSER_PROMPT: str = os.getenv(
        "IMAGE_PARSER_PROMPT",
        """
您是一名负责为图像检索任务生成摘要的助手。
1. 这些摘要将被嵌入并用于检索原始图像。
请提供简洁的图像摘要，确保其高度优化以利于检索
2. 提取图像中的所有文本内容。
不得遗漏页面上的任何信息。
3. 不要凭空捏造不存在的信息
请使用Markdown格式直接输出答案，
无需解释性文字，且开头不要使用Markdown分隔符```。
""",
    ).strip()

    # 文档处理配置
    SUPPORTED_FILE_TYPES: List[str] = [".pdf", ".txt", ".md", ".docx", ".doc"]
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")

    # PDF 多模态处理配置
    ENABLE_PDF_MULTIMODAL: bool = (
        os.getenv("ENABLE_PDF_MULTIMODAL", "true").lower() == "true"
    )
    PDF_EXTRACT_IMAGES: bool = os.getenv("PDF_EXTRACT_IMAGES", "true").lower() == "true"
    PDF_TABLE_STRATEGY: str = os.getenv("PDF_TABLE_STRATEGY", "lines")
    PDF_LOADER_MODE: str = os.getenv("PDF_LOADER_MODE", "single")

    # 文本分块配置
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1024"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # RAG特定配置
    DEFAULT_KNOWLEDGE_BASE: str = os.getenv("DEFAULT_KNOWLEDGE_BASE", "default")
    RAG_ENABLE_GRADING: bool = os.getenv("RAG_ENABLE_GRADING", "true").lower() == "true"
    RAG_ENABLE_REWRITE: bool = os.getenv("RAG_ENABLE_REWRITE", "true").lower() == "true"
    RAG_MAX_ITERATIONS: int = int(os.getenv("RAG_MAX_ITERATIONS", "3"))
    RAG_RETRIEVER_K: int = int(os.getenv("RAG_RETRIEVER_K", "4"))
    RAG_SIMILARITY_THRESHOLD: float = float(
        os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7")
    )

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "agentic_rag.log")
    ENABLE_DETAILED_LOGGING: bool = (
        os.getenv("ENABLE_DETAILED_LOGGING", "true").lower() == "true"
    )

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"  # 允许额外的环境变量

    def validate_configuration(self) -> List[str]:
        """
        验证配置的有效性

        Returns:
            配置问题列表，空列表表示配置正常
        """
        issues = []

        # 检查必需的API密钥
        if not self.LLM_API_KEY:
            issues.append("LLM_API_KEY is required for LLM models")

        if not self.IMAGE_PARSER_API_KEY:
            issues.append("IMAGE_PARSER_API_KEY is required for image processing")

        return issues

    def get_safe_config(self) -> Dict[str, Any]:
        """
        获取安全的配置信息（隐藏敏感信息）

        Returns:
            安全的配置字典
        """
        config = self.dict()

        # 隐藏敏感信息
        sensitive_keys = ["LLM_API_KEY", "IMAGE_PARSER_API_KEY", "SECRET_KEY"]

        for key in sensitive_keys:
            if key in config and config[key]:
                config[key] = (
                    "***" + config[key][-4:] if len(config[key]) > 4 else "***"
                )

        return config


# 创建全局settings实例
settings = Settings()
