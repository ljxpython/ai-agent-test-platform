"""
Milvus向量数据库客户端
提供向量存储、检索和管理功能
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pymilvus import DataType, MilvusClient

try:
    from .config import get_config
except ImportError:
    from config import get_config


class MilvusVectorClient:
    """Milvus向量数据库客户端"""

    def __init__(self, config=None):
        self.config = config or get_config().milvus
        self.client = None
        self._connected = False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()

    def connect(self):
        """连接到Milvus服务器"""
        if self._connected:
            return

        try:
            self.client = MilvusClient(
                uri=f"http://{self.config.host}:{self.config.port}"
            )
            self._connected = True
            logger.info(
                f"成功连接到Milvus服务器: {self.config.host}:{self.config.port}"
            )

            # 检查服务器状态
            try:
                collections = self.client.list_collections()
                logger.info(f"Milvus连接成功，当前集合数量: {len(collections)}")
            except Exception as e:
                logger.warning(f"获取服务器信息失败: {e}")

        except Exception as e:
            logger.error(f"连接Milvus失败: {e}")
            raise

    def disconnect(self):
        """断开连接"""
        if self._connected:
            if self.client:
                self.client.close()
                self.client = None
            self._connected = False
            logger.info("已断开Milvus连接")

    def create_collection(self, drop_existing: bool = False) -> bool:
        """创建集合"""
        if not self._connected:
            self.connect()

        collection_name = self.config.collection_name

        # 检查集合是否存在
        if self.client.has_collection(collection_name):
            if drop_existing:
                logger.info(f"删除现有集合: {collection_name}")
                self.client.drop_collection(collection_name)
            else:
                logger.info(f"集合 {collection_name} 已存在，直接使用")
                return True

        try:
            # 使用MilvusClient创建集合的schema
            schema = self.client.create_schema(
                auto_id=True,
                enable_dynamic_field=True,
                description="RAG教学系统向量集合",
            )

            # 添加字段
            schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
            schema.add_field(
                field_name="text", datatype=DataType.VARCHAR, max_length=65535
            )
            schema.add_field(
                field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=768
            )
            schema.add_field(field_name="metadata", datatype=DataType.JSON)
            schema.add_field(field_name="timestamp", datatype=DataType.INT64)

            # 创建索引参数
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="embedding",
                index_type=self.config.index_type,
                metric_type=self.config.metric_type,
                params={"nlist": self.config.nlist},
            )

            # 创建集合
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema,
                index_params=index_params,
            )

            logger.info(f"成功创建集合: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            raise

    def load_collection(self):
        """加载集合到内存"""
        if not self._connected:
            raise ValueError("未连接到Milvus服务器")

        try:
            # MilvusClient会自动处理集合加载，无需显式调用
            logger.info(f"集合 {self.config.collection_name} 已准备就绪")

        except Exception as e:
            logger.error(f"准备集合失败: {e}")
            raise

    def insert_data(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadata_list: Optional[List[Dict]] = None,
    ) -> List[int]:
        """插入数据到集合"""
        if not self._connected:
            raise ValueError("未连接到Milvus服务器")

        if len(texts) != len(embeddings):
            raise ValueError("文本和嵌入向量数量不匹配")

        try:
            # 准备数据
            current_time = int(time.time() * 1000)  # 毫秒时间戳

            data = []
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                metadata = metadata_list[i] if metadata_list else {}

                data.append(
                    {
                        "text": text,
                        "embedding": embedding,
                        "metadata": metadata,
                        "timestamp": current_time,
                    }
                )

            # 插入数据
            logger.info(f"插入 {len(data)} 条数据到集合")
            insert_result = self.client.insert(
                collection_name=self.config.collection_name, data=data
            )

            logger.info(f"数据插入成功，插入条数: {insert_result['insert_count']}")
            return insert_result.get("ids", [])

        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            raise

    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        if not self._connected:
            raise ValueError("未连接到Milvus服务器")

        try:
            # 搜索参数
            search_params = {
                "metric_type": self.config.metric_type,
                "params": {"nprobe": self.config.nprobe},
            }

            # 执行搜索
            logger.debug(f"搜索相似向量，top_k: {top_k}")
            start_time = time.time()

            results = self.client.search(
                collection_name=self.config.collection_name,
                data=[query_embedding],
                anns_field="embedding",
                search_params=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=["text", "metadata", "timestamp"],
            )

            search_time = time.time() - start_time
            logger.debug(f"搜索完成，耗时: {search_time:.3f}s")

            # 处理结果
            formatted_results = []
            for hit in results[0]:
                formatted_results.append(
                    {
                        "id": hit.get("id"),
                        "text": hit.get("entity", {}).get("text"),
                        "metadata": hit.get("entity", {}).get("metadata", {}),
                        "timestamp": hit.get("entity", {}).get("timestamp"),
                        "similarity_score": float(hit.get("score", 0)),
                        "distance": (
                            float(hit.get("distance", 0))
                            if hit.get("distance") is not None
                            else None
                        ),
                    }
                )

            logger.info(f"找到 {len(formatted_results)} 个相似结果")
            return formatted_results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        if not self._connected:
            return {}

        try:
            # 获取集合信息
            collection_info = self.client.describe_collection(
                self.config.collection_name
            )

            # 获取集合统计
            stats = self.client.get_collection_stats(self.config.collection_name)

            return {
                "collection_name": self.config.collection_name,
                "row_count": stats.get("row_count", 0),
                "data_size": stats.get("data_size", 0),
                "index_size": stats.get("index_size", 0),
                "schema": str(collection_info),
            }

        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {}

    def delete_by_expr(self, expr: str) -> int:
        """根据表达式删除数据"""
        if not self._connected:
            raise ValueError("未连接到Milvus服务器")

        try:
            result = self.client.delete(
                collection_name=self.config.collection_name, filter=expr
            )
            logger.info(f"删除数据成功，删除条数: {result.get('delete_count', 0)}")
            return result.get("delete_count", 0)

        except Exception as e:
            logger.error(f"删除数据失败: {e}")
            raise

    def drop_collection(self):
        """删除集合"""
        if not self._connected:
            self.connect()

        try:
            if self.client.has_collection(self.config.collection_name):
                self.client.drop_collection(self.config.collection_name)
                logger.info(f"集合 {self.config.collection_name} 已删除")
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            raise


# 便捷函数
def create_milvus_client() -> MilvusVectorClient:
    """创建并连接Milvus客户端"""
    client = MilvusVectorClient()
    client.connect()
    return client


if __name__ == "__main__":
    # 测试代码
    with MilvusVectorClient() as client:
        # 创建集合
        client.create_collection(drop_existing=True)

        # 测试数据
        texts = ["这是测试文本1", "这是测试文本2"]
        embeddings = [[0.1] * 768, [0.2] * 768]  # 模拟嵌入向量
        metadata = [{"source": "test1"}, {"source": "test2"}]

        # 插入数据
        ids = client.insert_data(texts, embeddings, metadata)
        print(f"插入数据ID: {ids}")

        # 等待一段时间确保数据已索引
        import time

        time.sleep(2)

        # 搜索测试
        query_embedding = [0.15] * 768
        results = client.search_similar(query_embedding, top_k=2)
        print(f"搜索结果: {len(results)} 条")

        # 统计信息
        stats = client.get_collection_stats()
        print(f"集合统计: {stats}")
