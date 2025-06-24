"""
查询引擎模块
基于LlamaIndex的查询引擎实现，整合向量检索和LLM生成
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# 设置项目路径
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import BaseNode, NodeWithScore, QueryBundle
from loguru import logger

from examples.conf.rag_config import RAGConfig
from examples.llama_rag_system_demo.embedding_generator import EmbeddingGenerator
from examples.llama_rag_system_demo.llm_service import LLMService
from examples.llama_rag_system_demo.vector_store import MilvusVectorDB


@dataclass
class QueryResult:
    """查询结果数据结构"""

    query: str
    answer: str
    retrieved_nodes: List[NodeWithScore]
    response_time: float
    metadata: Dict[str, Any]


class RAGQueryEngine:
    """RAG查询引擎"""

    def __init__(self, config: RAGConfig):
        """
        初始化查询引擎

        Args:
            config: RAG配置
        """
        self.config = config
        self.vector_db: MilvusVectorDB = None
        self.embedding_generator: EmbeddingGenerator = None
        self.llm_service: LLMService = None
        self.index: VectorStoreIndex = None
        self.query_engine: RetrieverQueryEngine = None
        self._initialized = False

        logger.info("🔧 RAG查询引擎初始化")

    async def initialize(self):
        """初始化查询引擎"""
        if self._initialized:
            return

        logger.info("🚀 正在初始化RAG查询引擎...")

        try:
            # 初始化向量数据库
            self.vector_db = MilvusVectorDB(self.config)
            self.vector_db.initialize()

            # 初始化嵌入生成器
            self.embedding_generator = EmbeddingGenerator(self.config)
            await self.embedding_generator.initialize()

            # 初始化LLM服务
            self.llm_service = LLMService(self.config)
            self.llm_service.initialize()

            # 创建向量索引
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_db.vector_store,
                embed_model=self.embedding_generator.embedding_model,
            )

            # 创建检索器
            retriever = VectorIndexRetriever(
                index=self.index, similarity_top_k=self.config.top_k
            )

            # 注意：由于我们使用的是简化的LLM包装器，这里暂时不使用LlamaIndex的查询引擎
            # 而是在query方法中手动实现RAG流程
            self.retriever = retriever

            self._initialized = True
            logger.success("✅ RAG查询引擎初始化完成")

        except Exception as e:
            logger.error(f"❌ RAG查询引擎初始化失败: {e}")
            raise

    async def query(self, query_text: str, **kwargs) -> QueryResult:
        """
        执行RAG查询

        Args:
            query_text: 查询文本
            **kwargs: 其他参数

        Returns:
            QueryResult: 查询结果
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"🔍 执行RAG查询: {query_text}")
        start_time = time.time()

        try:
            # 手动实现RAG流程
            # 1. 检索相关文档
            retrieved_nodes = await self.retrieve_only(query_text)

            # 2. 生成回答
            if retrieved_nodes:
                answer = await self.generate_answer(query_text, retrieved_nodes)
            else:
                answer = "抱歉，没有找到相关信息来回答您的问题。"

            # 计算响应时间
            response_time = time.time() - start_time

            # 构建查询结果
            result = QueryResult(
                query=query_text,
                answer=answer,
                retrieved_nodes=retrieved_nodes,
                response_time=response_time,
                metadata={
                    "num_retrieved": len(retrieved_nodes),
                    "top_k": self.config.top_k,
                    "similarity_threshold": self.config.similarity_threshold,
                },
            )

            logger.success(f"✅ RAG查询完成 - 耗时: {response_time:.3f}s")
            return result

        except Exception as e:
            logger.error(f"❌ RAG查询失败: {e}")
            raise

    async def retrieve_only(
        self, query_text: str, top_k: Optional[int] = None
    ) -> List[NodeWithScore]:
        """
        仅执行检索，不生成回答

        Args:
            query_text: 查询文本
            top_k: 检索数量

        Returns:
            List[NodeWithScore]: 检索到的节点
        """
        if not self._initialized:
            await self.initialize()

        top_k = top_k or self.config.top_k
        logger.info(f"🔍 执行检索: {query_text} (top_k={top_k})")

        try:
            # 创建查询包
            query_bundle = QueryBundle(query_str=query_text)

            # 执行检索
            retrieved_nodes = self.retriever.retrieve(query_bundle)

            # 过滤低相似度结果
            filtered_nodes = []
            for node in retrieved_nodes:
                if node.score >= self.config.similarity_threshold:
                    filtered_nodes.append(node)
                else:
                    logger.debug(f"过滤低相似度节点: {node.score:.3f}")

            logger.success(
                f"✅ 检索完成: {len(filtered_nodes)}/{len(retrieved_nodes)} 个节点"
            )
            return filtered_nodes

        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            raise

    async def generate_answer(
        self, query_text: str, context_nodes: List[NodeWithScore]
    ) -> str:
        """
        基于检索到的节点生成回答

        Args:
            query_text: 查询文本
            context_nodes: 上下文节点

        Returns:
            str: 生成的回答
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"💭 基于 {len(context_nodes)} 个节点生成回答")

        try:
            # 构建上下文
            context_parts = []
            for i, node in enumerate(context_nodes):
                context_parts.append(f"[文档{i+1}] {node.node.text}")

            context = "\n\n".join(context_parts)

            # 生成回答
            answer = self.llm_service.generate_rag_response(query_text, context)

            logger.success("✅ 回答生成完成")
            return answer

        except Exception as e:
            logger.error(f"❌ 回答生成失败: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        获取查询引擎统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "initialized": self._initialized,
            "config": {
                "top_k": self.config.top_k,
                "similarity_threshold": self.config.similarity_threshold,
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
            },
        }

        if self.vector_db:
            stats["vector_db"] = self.vector_db.get_stats()

        if self.llm_service:
            stats["llm"] = self.llm_service.get_model_info()

        return stats

    async def close(self):
        """清理资源"""
        if self.embedding_generator:
            await self.embedding_generator.close()

        if self.llm_service:
            self.llm_service.close()

        if self.vector_db:
            self.vector_db.close()

        self._initialized = False
        logger.info("🔄 RAG查询引擎资源清理完成")


async def create_query_engine(config: RAGConfig) -> RAGQueryEngine:
    """
    创建并初始化查询引擎

    Args:
        config: RAG配置

    Returns:
        RAGQueryEngine: 初始化后的查询引擎
    """
    engine = RAGQueryEngine(config)
    await engine.initialize()
    return engine


if __name__ == "__main__":
    # 测试代码
    import asyncio

    from examples.conf.rag_config import get_rag_config

    async def test_query_engine():
        config = get_rag_config()
        engine = await create_query_engine(config)

        # 获取统计信息
        stats = engine.get_stats()
        print(f"查询引擎统计: {stats}")

        await engine.close()

    asyncio.run(test_query_engine())
