"""
LlamaIndex RAG系统 - 主入口文件
简化的RAG系统实现，基于LlamaIndex框架
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from llama_index.core.schema import BaseNode
from loguru import logger

from examples.conf.rag_config import RAGConfig, get_rag_config

# 设置项目路径
from . import utils
from .data_loader import DocumentLoader
from .embedding_generator import EmbeddingGenerator
from .llm_service import LLMService
from .query_engine import QueryResult, RAGQueryEngine
from .vector_store import MilvusVectorDB


class RAGSystem:
    """简化的RAG系统主类"""

    def __init__(self, config: Optional[RAGConfig] = None):
        """初始化RAG系统"""
        self.config = config or get_rag_config()
        self.query_engine: RAGQueryEngine = None
        self._initialized = False

        logger.info("🚀 RAG系统初始化")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()

    async def initialize(self):
        """初始化RAG系统"""
        if self._initialized:
            return

        logger.info("🔧 正在初始化RAG系统...")

        try:
            self.query_engine = RAGQueryEngine(self.config)
            await self.query_engine.initialize()

            self._initialized = True
            logger.success("✅ RAG系统初始化完成")

        except Exception as e:
            logger.error(f"❌ RAG系统初始化失败: {e}")
            raise

    async def setup_collection(self, overwrite: bool = False):
        """设置向量集合"""
        if not self._initialized:
            await self.initialize()

        logger.info("📦 设置向量集合...")
        self.query_engine.vector_db.create_collection(overwrite=overwrite)
        logger.success("✅ 向量集合设置完成")

    async def add_text(
        self, text: str, metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """添加文本到知识库"""
        if not self._initialized:
            await self.initialize()

        logger.info(f"📝 添加文本 - 长度: {len(text)}")

        try:
            # 1. 加载并分割文档
            loader = DocumentLoader(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
            )
            documents = loader.load_from_text(text, metadata)
            nodes = loader.split_documents(documents)

            if not nodes:
                logger.warning("文本分割为空")
                return 0

            # 2. 生成嵌入向量
            texts = [node.text for node in nodes]
            embeddings = await self.query_engine.embedding_generator.embed_texts(texts)

            # 3. 设置节点的嵌入向量
            for node, embedding in zip(nodes, embeddings):
                node.embedding = embedding

            # 4. 添加到向量数据库
            node_ids = self.query_engine.vector_db.add_nodes(nodes)

            logger.success(f"✅ 文本添加完成 - 节点数: {len(node_ids)}")
            return len(node_ids)

        except Exception as e:
            logger.error(f"❌ 文本添加失败: {e}")
            raise

    async def add_file(self, file_path: Union[str, Path]) -> int:
        """从文件添加文档"""
        if not self._initialized:
            await self.initialize()

        logger.info(f"📄 添加文件: {file_path}")

        try:
            # 1. 加载并分割文档
            loader = DocumentLoader(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
            )
            nodes = loader.load_and_split(file_path)

            if not nodes:
                logger.warning("文件为空，跳过处理")
                return 0

            # 2. 生成嵌入向量
            texts = [node.text for node in nodes]
            embeddings = await self.query_engine.embedding_generator.embed_texts(texts)

            # 3. 设置节点的嵌入向量
            for node, embedding in zip(nodes, embeddings):
                node.embedding = embedding

            # 4. 添加到向量数据库
            node_ids = self.query_engine.vector_db.add_nodes(nodes)

            logger.success(f"✅ 文件添加完成 - 节点数: {len(node_ids)}")
            return len(node_ids)

        except Exception as e:
            logger.error(f"❌ 文件添加失败: {e}")
            raise

    async def query(self, question: str, **kwargs) -> QueryResult:
        """执行RAG查询"""
        if not self._initialized:
            await self.initialize()

        return await self.query_engine.query(question, **kwargs)

    async def chat(self, message: str) -> str:
        """简单的聊天接口"""
        result = await self.query(message)
        return result.answer

    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        if not self._initialized:
            return {"initialized": False}

        return self.query_engine.get_stats()

    async def clear_data(self):
        """清空所有数据"""
        if not self._initialized:
            await self.initialize()

        logger.warning("🗑️ 清空所有数据...")
        self.query_engine.vector_db.delete_collection()
        await self.setup_collection()
        logger.success("✅ 数据清空完成")

    async def cleanup(self):
        """清理资源"""
        if self.query_engine:
            await self.query_engine.close()

        self._initialized = False
        logger.info("🔄 RAG系统资源清理完成")


# 便捷函数
async def create_rag_system(config: Optional[RAGConfig] = None) -> RAGSystem:
    """创建并初始化RAG系统"""
    rag = RAGSystem(config)
    await rag.initialize()
    return rag


if __name__ == "__main__":
    # 简单测试
    async def test():
        async with RAGSystem() as rag:
            await rag.setup_collection(overwrite=True)

            # 添加测试文本
            await rag.add_text("人工智能是计算机科学的一个分支。")

            # 测试查询
            answer = await rag.chat("什么是人工智能？")
            print(f"回答: {answer}")

    asyncio.run(test())
