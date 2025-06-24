"""
RAG系统配置文件
包含Milvus、Ollama等服务的配置参数
"""

import os
from dataclasses import dataclass
from typing import Any, Dict

from examples.conf.config import settings


@dataclass
class MilvusConfig:
    """Milvus向量数据库配置"""

    host: str = settings.milvus.host
    port: int = settings.milvus.port
    collection_name: str = "rag_tutorial_collection"
    dimension: int = 768  # nomic-embed-text的实际维度
    metric_type: str = "COSINE"  # Cosine Similarity
    index_type: str = "IVF_FLAT"
    nlist: int = 1024
    nprobe: int = 10


@dataclass
class OllamaConfig:
    """Ollama嵌入模型配置"""

    base_url: str = settings.ollama.base_url
    model_name: str = "nomic-embed-text"  # 推荐的嵌入模型
    timeout: int = 30
    max_retries: int = 3


@dataclass
class DocumentConfig:
    """文档处理配置"""

    chunk_size: int = 512
    chunk_overlap: int = 50
    max_chunks_per_doc: int = 100
    supported_formats: list = None

    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = [".txt", ".md", ".pdf", ".docx"]


@dataclass
class RetrievalConfig:
    """检索配置"""

    top_k: int = 5
    similarity_threshold: float = 0.3
    rerank_top_k: int = 10
    enable_rerank: bool = True


@dataclass
class RAGConfig:
    """RAG系统总配置"""

    milvus: MilvusConfig
    ollama: OllamaConfig
    document: DocumentConfig
    retrieval: RetrievalConfig

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "rag_tutorial.log"

    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1小时

    def __init__(self):
        self.milvus = MilvusConfig()
        self.ollama = OllamaConfig()
        self.document = DocumentConfig()
        self.retrieval = RetrievalConfig()


# 全局配置实例
config = RAGConfig()


def get_config() -> RAGConfig:
    """获取配置实例"""
    return config


def update_config_from_env():
    """从环境变量更新配置"""
    # Milvus配置
    config.milvus.host = os.getenv("MILVUS_HOST", config.milvus.host)
    config.milvus.port = int(os.getenv("MILVUS_PORT", config.milvus.port))
    config.milvus.collection_name = os.getenv(
        "MILVUS_COLLECTION_NAME", config.milvus.collection_name
    )

    # Ollama配置
    config.ollama.base_url = os.getenv("OLLAMA_BASE_URL", config.ollama.base_url)
    config.ollama.model_name = os.getenv("OLLAMA_MODEL_NAME", config.ollama.model_name)

    # 日志配置
    config.log_level = os.getenv("LOG_LEVEL", config.log_level)


def print_config():
    """打印当前配置"""
    print("=== RAG系统配置 ===")
    print(f"Milvus服务器: {config.milvus.host}:{config.milvus.port}")
    print(f"Milvus集合: {config.milvus.collection_name}")
    print(f"向量维度: {config.milvus.dimension}")
    print(f"Ollama服务: {config.ollama.base_url}")
    print(f"嵌入模型: {config.ollama.model_name}")
    print(f"文档分块大小: {config.document.chunk_size}")
    print(f"检索Top-K: {config.retrieval.top_k}")
    print("==================")


if __name__ == "__main__":
    update_config_from_env()
    print_config()
