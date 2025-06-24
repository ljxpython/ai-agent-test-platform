"""
RAG系统配置管理
基于项目现有配置系统，为RAG系统提供统一的配置管理
"""

from dataclasses import dataclass
from typing import Optional

from examples.conf.config import settings


@dataclass
class MilvusConfig:
    """Milvus向量数据库配置"""

    host: str
    port: int
    collection_name: str
    dimension: int = 768  # nomic-embed-text的向量维度

    @classmethod
    def from_settings(cls):
        """从settings中创建配置"""
        return cls(
            host=settings.milvus.host,
            port=settings.milvus.port,
            collection_name=settings.milvus.collection_name,
            dimension=settings.nomic_embed_text.dimension,
        )


@dataclass
class OllamaConfig:
    """Ollama服务配置"""

    base_url: str
    embedding_model: str

    @classmethod
    def from_settings(cls):
        """从settings中创建配置"""
        return cls(
            base_url=settings.ollama.base_url,
            embedding_model=settings.ollama.model_name,
        )


@dataclass
class DeepSeekConfig:
    """DeepSeek大语言模型配置"""

    model: str
    api_key: str
    base_url: str

    @classmethod
    def from_settings(cls):
        """从settings中创建配置"""
        return cls(
            model=settings.aimodel.model,
            api_key=settings.aimodel.api_key,
            base_url=settings.aimodel.base_url,
        )


@dataclass
class RAGConfig:
    """RAG系统总配置"""

    milvus: MilvusConfig
    ollama: OllamaConfig
    deepseek: DeepSeekConfig

    # 检索参数
    top_k: int = 5
    similarity_threshold: float = 0.7

    # 文档处理参数
    chunk_size: int = 1000
    chunk_overlap: int = 200

    @classmethod
    def from_settings(cls):
        """从settings中创建完整配置"""
        return cls(
            milvus=MilvusConfig.from_settings(),
            ollama=OllamaConfig.from_settings(),
            deepseek=DeepSeekConfig.from_settings(),
        )


def get_rag_config() -> RAGConfig:
    """获取RAG系统配置"""
    return RAGConfig.from_settings()


if __name__ == "__main__":
    # 测试配置
    config = get_rag_config()
    print("RAG系统配置:")
    print(f"Milvus: {config.milvus.host}:{config.milvus.port}")
    print(f"Ollama: {config.ollama.base_url}")
    print(f"DeepSeek: {config.deepseek.model}")
    print(f"嵌入模型: {config.ollama.embedding_model}")
