"""
RAG系统核心类
整合文档处理、向量化、存储和检索功能
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from .config import get_config
from .document_processor import DocumentChunk, DocumentProcessor
from .milvus_client import MilvusVectorClient
from .ollama_embeddings import OllamaEmbeddingClient


@dataclass
class RetrievalResult:
    """检索结果数据结构"""

    text: str
    similarity_score: float
    metadata: Dict[str, Any]
    chunk_id: str
    source: str


@dataclass
class RAGResponse:
    """RAG响应数据结构"""

    query: str
    retrieved_chunks: List[RetrievalResult]
    context: str
    response_time: float
    total_chunks: int


class RAGSystem:
    """RAG系统主类"""

    def __init__(self, config=None):
        self.config = config or get_config()

        # 初始化组件
        self.embedding_client = None
        self.vector_client = None
        self.document_processor = DocumentProcessor(self.config)

        # 状态标记
        self._initialized = False

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

        logger.info("正在初始化RAG系统...")

        try:
            # 初始化嵌入客户端
            self.embedding_client = OllamaEmbeddingClient(self.config.ollama)
            await self.embedding_client.initialize()

            # 初始化向量数据库客户端
            self.vector_client = MilvusVectorClient(self.config.milvus)
            self.vector_client.connect()

            self._initialized = True
            logger.info("RAG系统初始化完成")

        except Exception as e:
            logger.error(f"RAG系统初始化失败: {e}")
            raise

    async def cleanup(self):
        """清理资源"""
        if self.embedding_client:
            await self.embedding_client.close()

        if self.vector_client:
            self.vector_client.disconnect()

        self._initialized = False
        logger.info("RAG系统资源清理完成")

    async def setup_collection(self, drop_existing: bool = False):
        """设置向量集合"""
        if not self._initialized:
            await self.initialize()

        logger.info("设置向量集合...")

        # 创建集合
        self.vector_client.create_collection(drop_existing=drop_existing)

        # 加载集合到内存
        self.vector_client.load_collection()

        logger.info("向量集合设置完成")

    async def add_documents_from_file(self, file_path: str) -> int:
        """从文件添加文档"""
        if not self._initialized:
            await self.initialize()

        logger.info(f"开始处理文件: {file_path}")
        start_time = time.time()

        try:
            # 1. 加载和分块文档
            logger.info("步骤1: 加载和分块文档")
            content = self.document_processor.load_document(file_path)
            chunks = self.document_processor.split_text_into_chunks(content, file_path)

            if not chunks:
                logger.warning("文档分块为空，跳过处理")
                return 0

            logger.info(f"文档分块完成，生成 {len(chunks)} 个块")

            # 2. 生成嵌入向量
            logger.info("步骤2: 生成嵌入向量")
            texts = [chunk.text for chunk in chunks]
            embeddings = await self.embedding_client.embed_texts(texts)

            # 3. 存储到向量数据库
            logger.info("步骤3: 存储到向量数据库")
            metadata_list = [chunk.metadata for chunk in chunks]

            # 添加额外的元数据
            for i, chunk in enumerate(chunks):
                metadata_list[i].update(
                    {
                        "chunk_id": chunk.chunk_id,
                        "file_path": file_path,
                        "processing_time": time.time(),
                    }
                )

            ids = self.vector_client.insert_data(texts, embeddings, metadata_list)

            processing_time = time.time() - start_time
            logger.info(
                f"文件处理完成，耗时: {processing_time:.2f}s，插入 {len(ids)} 条记录"
            )

            return len(ids)

        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            raise

    async def add_documents_from_directory(self, directory_path: str) -> int:
        """从目录批量添加文档"""
        if not self._initialized:
            await self.initialize()

        logger.info(f"开始批量处理目录: {directory_path}")
        start_time = time.time()

        try:
            # 处理目录中的所有文档
            all_chunks = self.document_processor.process_directory(directory_path)

            if not all_chunks:
                logger.warning("目录中没有找到有效文档")
                return 0

            logger.info(f"目录处理完成，总共 {len(all_chunks)} 个文档块")

            # 批量生成嵌入向量
            logger.info("开始批量向量化...")
            texts = [chunk.text for chunk in all_chunks]
            embeddings = await self.embedding_client.embed_texts(texts, batch_size=20)

            # 批量存储
            logger.info("开始批量存储...")
            metadata_list = []
            for chunk in all_chunks:
                metadata = chunk.metadata.copy()
                metadata.update(
                    {"chunk_id": chunk.chunk_id, "processing_time": time.time()}
                )
                metadata_list.append(metadata)

            ids = self.vector_client.insert_data(texts, embeddings, metadata_list)

            processing_time = time.time() - start_time
            logger.info(
                f"目录处理完成，耗时: {processing_time:.2f}s，插入 {len(ids)} 条记录"
            )

            return len(ids)

        except Exception as e:
            logger.error(f"批量处理目录失败: {e}")
            raise

    async def add_text_directly(
        self, text: str, source: str = "direct_input", metadata: Optional[Dict] = None
    ) -> int:
        """直接添加文本"""
        if not self._initialized:
            await self.initialize()

        logger.info(f"直接添加文本，长度: {len(text)}")

        try:
            # 分块处理
            chunks = self.document_processor.split_text_into_chunks(text, source)

            if not chunks:
                logger.warning("文本分块为空")
                return 0

            # 生成嵌入向量
            texts = [chunk.text for chunk in chunks]
            embeddings = await self.embedding_client.embed_texts(texts)

            # 准备元数据
            metadata_list = []
            for chunk in chunks:
                chunk_metadata = chunk.metadata.copy()
                if metadata:
                    chunk_metadata.update(metadata)
                chunk_metadata.update(
                    {"chunk_id": chunk.chunk_id, "processing_time": time.time()}
                )
                metadata_list.append(chunk_metadata)

            # 存储
            ids = self.vector_client.insert_data(texts, embeddings, metadata_list)

            logger.info(f"文本添加完成，插入 {len(ids)} 条记录")
            return len(ids)

        except Exception as e:
            logger.error(f"添加文本失败: {e}")
            raise

    async def retrieve(
        self, query: str, top_k: Optional[int] = None, filter_expr: Optional[str] = None
    ) -> List[RetrievalResult]:
        """检索相关文档"""
        if not self._initialized:
            await self.initialize()

        top_k = top_k or self.config.retrieval.top_k

        logger.info(f"开始检索，查询: '{query}', top_k: {top_k}")
        start_time = time.time()

        try:
            # 1. 向量化查询
            query_embedding = await self.embedding_client.embed_text(query)

            # 2. 向量搜索
            search_results = self.vector_client.search_similar(
                query_embedding, top_k=top_k, filter_expr=filter_expr
            )

            # 3. 转换结果格式
            retrieval_results = []
            for result in search_results:
                # 过滤低相似度结果
                if (
                    result["similarity_score"]
                    < self.config.retrieval.similarity_threshold
                ):
                    continue

                retrieval_result = RetrievalResult(
                    text=result["text"],
                    similarity_score=result["similarity_score"],
                    metadata=result["metadata"],
                    chunk_id=result["metadata"].get("chunk_id", ""),
                    source=result["metadata"].get("source", ""),
                )
                retrieval_results.append(retrieval_result)

            retrieval_time = time.time() - start_time
            logger.info(
                f"检索完成，耗时: {retrieval_time:.3f}s，返回 {len(retrieval_results)} 个结果"
            )

            return retrieval_results

        except Exception as e:
            logger.error(f"检索失败: {e}")
            raise

    async def query(self, query: str, top_k: Optional[int] = None) -> RAGResponse:
        """完整的RAG查询流程"""
        if not self._initialized:
            await self.initialize()

        logger.info(f"开始RAG查询: '{query}'")
        start_time = time.time()

        try:
            # 检索相关文档
            retrieved_chunks = await self.retrieve(query, top_k)

            # 构建上下文
            context_parts = []
            for i, chunk in enumerate(retrieved_chunks):
                context_parts.append(f"[文档{i+1}] {chunk.text}")

            context = "\n\n".join(context_parts)

            # 获取集合统计信息
            stats = self.vector_client.get_collection_stats()
            total_chunks = stats.get("row_count", 0)

            response_time = time.time() - start_time

            response = RAGResponse(
                query=query,
                retrieved_chunks=retrieved_chunks,
                context=context,
                response_time=response_time,
                total_chunks=total_chunks,
            )

            logger.info(f"RAG查询完成，耗时: {response_time:.3f}s")
            return response

        except Exception as e:
            logger.error(f"RAG查询失败: {e}")
            raise

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        stats = {
            "initialized": self._initialized,
            "embedding_client": self.embedding_client is not None,
            "vector_client": self.vector_client is not None,
        }

        if self.vector_client:
            stats.update(self.vector_client.get_collection_stats())

        return stats

    async def clear_all_data(self):
        """清空所有数据"""
        if not self._initialized:
            await self.initialize()

        logger.warning("正在清空所有数据...")
        self.vector_client.drop_collection()
        await self.setup_collection()
        logger.info("数据清空完成")


# 便捷函数
async def create_rag_system() -> RAGSystem:
    """创建并初始化RAG系统"""
    rag = RAGSystem()
    await rag.initialize()
    return rag


if __name__ == "__main__":
    # 测试代码
    async def test_rag_system():
        async with RAGSystem() as rag:
            # 设置集合
            await rag.setup_collection(drop_existing=True)

            # 添加测试文本
            test_text = """
            人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
            机器学习是人工智能的一个子集，它使计算机能够从数据中学习而无需明确编程。
            深度学习是机器学习的一个子集，使用神经网络来模拟人脑的工作方式。
            """

            await rag.add_text_directly(test_text, "test_doc")

            # 测试查询
            response = await rag.query("什么是机器学习？")

            print(f"查询: {response.query}")
            print(f"检索到 {len(response.retrieved_chunks)} 个相关文档")
            print(f"响应时间: {response.response_time:.3f}s")
            print(f"上下文:\n{response.context}")

    asyncio.run(test_rag_system())
