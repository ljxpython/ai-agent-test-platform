"""
RAG检索服务
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import create_retriever_tool
from langchain_milvus import Milvus
from langchain_ollama import OllamaEmbeddings

sys.path.append(str(Path(__file__).parent.parent))
from llms import get_default_model

try:
    # 尝试相对导入
    from .config import (
        EMBEDDING_BASE_URL,
        EMBEDDING_MODEL,
        MILVUS_COLLECTION_NAME,
        MILVUS_URI,
    )
except ImportError:
    # 绝对导入
    from config import (
        EMBEDDING_BASE_URL,
        EMBEDDING_MODEL,
        MILVUS_COLLECTION_NAME,
        MILVUS_URI,
    )


class RAGService:
    """RAG检索服务"""

    def __init__(self):
        self.embedding = OllamaEmbeddings(
            model=EMBEDDING_MODEL, base_url=EMBEDDING_BASE_URL, temperature=0
        )

        self.vector_store = Milvus(
            embedding_function=self.embedding,
            connection_args={"uri": MILVUS_URI},
            collection_name=MILVUS_COLLECTION_NAME,
            index_params={"index_type": "FLAT", "metric_type": "L2"},
        )

    def similarity_search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            搜索结果列表
        """
        results = self.vector_store.similarity_search(query, k=k)

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": getattr(doc, "score", None),
            }
            for doc in results
        ]

    def similarity_search_with_score(
        self, query: str, k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        带分数的相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            搜索结果列表(包含分数)
        """
        results = self.vector_store.similarity_search_with_score(query, k=k)

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
            for doc, score in results
        ]

    def create_retriever(self, search_type: str = "similarity", k: int = 4):
        """
        创建检索器

        Args:
            search_type: 搜索类型 (similarity, mmr, similarity_score_threshold)
            k: 返回结果数量

        Returns:
            检索器
        """
        retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k},
        )
        return retriever

    def create_retriever_tool(self):
        """
        创建检索工具

        Returns:
            检索工具
        """
        retriever = self.create_retriever()

        retriever_tool = create_retriever_tool(
            retriever,
            "retrieve_document",
            "擅长知识文档检索,可以从知识库中检索相关信息",
        )
        return retriever_tool

    def create_rag_agent(self):
        """
        创建RAG Agent

        Returns:
            Agent实例
        """
        retriever_tool = self.create_retriever_tool()

        agent = create_agent(
            model=get_default_model(),
            tools=[retriever_tool],
            system_prompt="你是一位擅长文献检索和知识整合的大师。当检索不出知识时,要告知用户,而非根据自己的知识进行讲解。",
        )
        return agent

    def query_with_agent(self, question: str) -> Dict[str, Any]:
        """
        使用Agent进行问答

        Args:
            question: 问题

        Returns:
            回答结果
        """
        agent = self.create_rag_agent()

        message = HumanMessage(content=question)
        response = agent.invoke({"messages": message})

        # 提取回答
        messages = response.get("messages", [])
        answer = ""
        for msg in messages:
            if hasattr(msg, "content") and msg.content:
                answer = msg.content

        return {
            "question": question,
            "answer": answer,
            "messages": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content if hasattr(msg, "content") else str(msg),
                }
                for msg in messages
            ],
        }
