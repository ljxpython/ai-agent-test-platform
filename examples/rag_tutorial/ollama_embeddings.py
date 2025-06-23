"""
Ollama嵌入模型客户端
提供文本向量化服务
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union

import aiohttp
from loguru import logger

from .config import get_config


class OllamaEmbeddingClient:
    """Ollama嵌入模型客户端"""

    def __init__(self, config=None):
        self.config = config or get_config().ollama
        self.session = None
        self._model_info = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def initialize(self):
        """初始化客户端"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)

        # 检查模型是否可用
        await self._check_model_availability()
        logger.info(f"Ollama嵌入客户端初始化成功，模型: {self.config.model_name}")

    async def close(self):
        """关闭客户端"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _check_model_availability(self):
        """检查模型是否可用"""
        try:
            url = f"{self.config.base_url}/api/tags"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model["name"] for model in data.get("models", [])]

                    if self.config.model_name not in models:
                        logger.warning(
                            f"模型 {self.config.model_name} 不在可用模型列表中: {models}"
                        )
                        # 尝试拉取模型
                        await self._pull_model()
                    else:
                        logger.info(f"模型 {self.config.model_name} 可用")

                else:
                    raise Exception(f"无法连接到Ollama服务: {response.status}")

        except Exception as e:
            logger.error(f"检查模型可用性失败: {e}")
            raise

    async def _pull_model(self):
        """拉取模型"""
        logger.info(f"正在拉取模型: {self.config.model_name}")
        url = f"{self.config.base_url}/api/pull"
        payload = {"name": self.config.model_name}

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    # 流式读取拉取进度
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line.decode())
                                if "status" in data:
                                    logger.info(f"拉取进度: {data['status']}")
                                if data.get("status") == "success":
                                    logger.info("模型拉取完成")
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    raise Exception(f"拉取模型失败: {response.status}")

        except Exception as e:
            logger.error(f"拉取模型失败: {e}")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """对单个文本进行向量化"""
        if not self.session:
            await self.initialize()

        url = f"{self.config.base_url}/api/embeddings"
        payload = {"model": self.config.model_name, "prompt": text}

        for attempt in range(self.config.max_retries):
            try:
                start_time = time.time()
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        embedding = data.get("embedding", [])

                        if not embedding:
                            raise ValueError("返回的嵌入向量为空")

                        duration = time.time() - start_time
                        logger.debug(
                            f"文本向量化完成，耗时: {duration:.2f}s，维度: {len(embedding)}"
                        )
                        return embedding

                    else:
                        error_text = await response.text()
                        raise Exception(f"API请求失败: {response.status}, {error_text}")

            except Exception as e:
                logger.warning(f"向量化尝试 {attempt + 1} 失败: {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2**attempt)  # 指数退避

    async def embed_texts(
        self, texts: List[str], batch_size: int = 10
    ) -> List[List[float]]:
        """批量文本向量化"""
        if not texts:
            return []

        logger.info(f"开始批量向量化，文本数量: {len(texts)}")
        embeddings = []

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(
                f"处理批次 {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}"
            )

            # 并发处理批次内的文本
            tasks = [self.embed_text(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for j, result in enumerate(batch_embeddings):
                if isinstance(result, Exception):
                    logger.error(f"文本 {i + j} 向量化失败: {result}")
                    # 使用零向量作为占位符
                    embeddings.append([0.0] * self.get_embedding_dimension())
                else:
                    embeddings.append(result)

        logger.info(
            f"批量向量化完成，成功: {len([e for e in embeddings if any(e)])}/{len(texts)}"
        )
        return embeddings

    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        # nomic-embed-text模型的维度是768，但配置中设置为1024
        # 这里返回配置中的维度，实际使用时需要根据模型调整
        return 768  # nomic-embed-text的实际维度

    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if self._model_info:
            return self._model_info

        try:
            url = f"{self.config.base_url}/api/show"
            payload = {"name": self.config.model_name}

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    self._model_info = await response.json()
                    return self._model_info
                else:
                    logger.warning(f"无法获取模型信息: {response.status}")
                    return {}

        except Exception as e:
            logger.error(f"获取模型信息失败: {e}")
            return {}


# 便捷函数
async def create_embedding_client() -> OllamaEmbeddingClient:
    """创建并初始化嵌入客户端"""
    client = OllamaEmbeddingClient()
    await client.initialize()
    return client


async def embed_single_text(text: str) -> List[float]:
    """快速向量化单个文本"""
    async with OllamaEmbeddingClient() as client:
        return await client.embed_text(text)


async def embed_multiple_texts(texts: List[str]) -> List[List[float]]:
    """快速向量化多个文本"""
    async with OllamaEmbeddingClient() as client:
        return await client.embed_texts(texts)


if __name__ == "__main__":
    # 测试代码
    async def test_embedding():
        async with OllamaEmbeddingClient() as client:
            # 测试单个文本
            text = "这是一个测试文本"
            embedding = await client.embed_text(text)
            print(f"文本: {text}")
            print(f"向量维度: {len(embedding)}")
            print(f"向量前5个元素: {embedding[:5]}")

            # 测试批量文本
            texts = ["文本1", "文本2", "文本3"]
            embeddings = await client.embed_texts(texts)
            print(f"批量向量化结果: {len(embeddings)} 个向量")

    asyncio.run(test_embedding())
