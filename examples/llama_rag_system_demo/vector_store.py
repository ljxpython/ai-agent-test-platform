"""
Milvus向量数据库模块
基于LlamaIndex的Milvus向量存储实现
"""

from typing import Any, Dict, List, Optional

from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.vector_stores import VectorStoreQuery, VectorStoreQueryResult
from llama_index.vector_stores.milvus import MilvusVectorStore
from loguru import logger

from examples.conf.rag_config import RAGConfig

# 设置项目路径


class MilvusVectorDB:
    """Milvus向量数据库管理器"""

    def __init__(self, config: RAGConfig):
        """
        初始化Milvus向量数据库

        Args:
            config: RAG配置
        """
        self.config = config.milvus
        self.vector_store: MilvusVectorStore = None
        self._initialized = False

        logger.info(f"🗄️ Milvus向量数据库初始化 - {self.config.host}:{self.config.port}")

    def initialize(self):
        """初始化向量存储"""
        if self._initialized:
            return

        logger.info("🚀 正在连接Milvus向量数据库...")

        try:
            # 创建Milvus向量存储
            self.vector_store = MilvusVectorStore(
                host=self.config.host,
                port=self.config.port,
                collection_name=self.config.collection_name,
                dim=self.config.dimension,
                overwrite=False,  # 不覆盖现有集合
            )

            self._initialized = True
            logger.success("✅ Milvus向量数据库连接成功")

        except Exception as e:
            logger.error(f"❌ Milvus向量数据库连接失败: {e}")
            raise

    def create_collection(self, overwrite: bool = False):
        """
        创建集合

        Args:
            overwrite: 是否覆盖现有集合
        """
        if not self._initialized:
            self.initialize()

        logger.info(f"📦 创建集合: {self.config.collection_name}")

        try:
            if overwrite:
                # 重新创建向量存储以覆盖集合
                self.vector_store = MilvusVectorStore(
                    host=self.config.host,
                    port=self.config.port,
                    collection_name=self.config.collection_name,
                    dim=self.config.dimension,
                    overwrite=True,
                )

            logger.success("✅ 集合创建完成")

        except Exception as e:
            logger.error(f"❌ 集合创建失败: {e}")
            raise

    def add_nodes(self, nodes: List[BaseNode]) -> List[str]:
        """
        添加节点到向量数据库

        Args:
            nodes: 节点列表

        Returns:
            List[str]: 节点ID列表
        """
        if not self._initialized:
            self.initialize()

        if not nodes:
            logger.warning("⚠️ 节点列表为空，跳过添加")
            return []

        logger.info(f"📝 添加 {len(nodes)} 个节点到向量数据库")

        try:
            # 使用向量存储添加节点
            node_ids = self.vector_store.add(nodes)

            logger.success(f"✅ 节点添加完成: {len(node_ids)} 个")
            return node_ids

        except Exception as e:
            logger.error(f"❌ 节点添加失败: {e}")
            raise

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> VectorStoreQueryResult:
        """
        查询相似向量

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            filters: 过滤条件

        Returns:
            VectorStoreQueryResult: 查询结果
        """
        if not self._initialized:
            self.initialize()

        logger.info(f"🔍 向量查询 - top_k: {top_k}")

        try:
            # 创建查询对象
            query_obj = VectorStoreQuery(
                query_embedding=query_embedding, similarity_top_k=top_k, filters=filters
            )

            # 执行查询
            result = self.vector_store.query(query_obj)

            logger.success(f"✅ 查询完成: 返回 {len(result.nodes)} 个结果")
            return result

        except Exception as e:
            logger.error(f"❌ 向量查询失败: {e}")
            raise

    def delete_collection(self):
        """删除集合"""
        if not self._initialized:
            self.initialize()

        logger.warning(f"🗑️ 删除集合: {self.config.collection_name}")

        try:
            # 通过重新创建并覆盖来删除集合
            self.vector_store = MilvusVectorStore(
                host=self.config.host,
                port=self.config.port,
                collection_name=self.config.collection_name,
                dim=self.config.dimension,
                overwrite=True,
            )

            logger.success("✅ 集合删除完成")

        except Exception as e:
            logger.error(f"❌ 集合删除失败: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self._initialized:
            self.initialize()

        try:
            # 基本统计信息
            stats = {
                "collection_name": self.config.collection_name,
                "dimension": self.config.dimension,
                "host": self.config.host,
                "port": self.config.port,
                "initialized": self._initialized,
            }

            return stats

        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {"error": str(e)}

    def close(self):
        """关闭连接"""
        if self.vector_store:
            # LlamaIndex的MilvusVectorStore通常不需要显式关闭
            pass

        self._initialized = False
        logger.info("🔄 Milvus向量数据库连接关闭")


def create_vector_db(config: RAGConfig) -> MilvusVectorDB:
    """
    创建并初始化向量数据库

    Args:
        config: RAG配置

    Returns:
        MilvusVectorDB: 初始化后的向量数据库
    """
    vector_db = MilvusVectorDB(config)
    vector_db.initialize()
    return vector_db


if __name__ == "__main__":
    # 测试代码
    from examples.conf.rag_config import get_rag_config

    config = get_rag_config()
    print(config.milvus)
    vector_db = create_vector_db(config)

    # 创建测试节点
    test_nodes = [
        TextNode(
            text="人工智能是计算机科学的一个分支",
            metadata={"source": "test", "topic": "AI"},
        ),
        TextNode(
            text="机器学习是人工智能的子集", metadata={"source": "test", "topic": "ML"}
        ),
    ]

    # 测试添加节点
    try:
        # 创建集合
        vector_db.create_collection(overwrite=True)

        # 添加节点（需要先设置嵌入向量）
        # 注意：在实际使用中，节点应该已经包含嵌入向量
        print("向量数据库测试完成")

        # 获取统计信息
        stats = vector_db.get_stats()
        print(f"统计信息: {stats}")

    except Exception as e:
        print(f"测试失败: {e}")

    finally:
        vector_db.close()
