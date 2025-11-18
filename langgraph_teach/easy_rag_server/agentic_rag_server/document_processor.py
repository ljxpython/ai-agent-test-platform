"""
文档处理服务
负责文档解析、分块和向量化
"""

import sys
from pathlib import Path
from typing import List

from langchain_community.document_loaders.parsers import LLMImageBlobParser
from langchain_core.documents import Document
from langchain_milvus import Milvus
from langchain_ollama import OllamaEmbeddings
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.append(str(Path(__file__).parent.parent))
from llms import get_doubao_model

try:
    # 尝试相对导入
    from .config import (
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        EMBEDDING_BASE_URL,
        EMBEDDING_MODEL,
        MILVUS_COLLECTION_NAME,
        MILVUS_URI,
    )
except ImportError:
    # 绝对导入
    from config import (
        CHUNK_OVERLAP,
        CHUNK_SIZE,
        EMBEDDING_BASE_URL,
        EMBEDDING_MODEL,
        MILVUS_COLLECTION_NAME,
        MILVUS_URI,
    )


class DocumentProcessor:
    """文档处理器"""

    def __init__(self):
        self.embedding = OllamaEmbeddings(
            model=EMBEDDING_MODEL, base_url=EMBEDDING_BASE_URL, temperature=0
        )

        self.text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
        )

    def extract_pdf_text(
        self, pdf_path: str, extract_images: bool = True
    ) -> List[Document]:
        """
        提取PDF文本和图片内容

        Args:
            pdf_path: PDF文件路径
            extract_images: 是否提取图片

        Returns:
            文档列表
        """
        _PROMPT_IMAGES_TO_DESCRIPTION = (
            "您是一名负责为图像检索任务生成摘要的助手。"
            "1. 这些摘要将被嵌入并用于检索原始图像。"
            "请提供简洁的图像摘要,确保其高度优化以利于检索\n"
            "2. 提取图像中的所有文本内容。"
            "不得遗漏页面上的任何信息。\n"
            "3. 不要凭空捏造不存在的信息\n"
            "请使用Markdown格式直接输出答案,"
            "无需解释性文字,且开头不要使用Markdown分隔符```。"
        )

        if extract_images:
            llm_parser = LLMImageBlobParser(
                model=get_doubao_model(),
                prompt=_PROMPT_IMAGES_TO_DESCRIPTION,
            )

            loader = PyMuPDF4LLMLoader(
                pdf_path,
                mode="single",
                extract_images=True,
                table_strategy="lines",
                images_parser=llm_parser,
            )
        else:
            loader = PyMuPDF4LLMLoader(
                pdf_path, mode="single", extract_images=False, table_strategy="lines"
            )

        documents = loader.load()
        return documents

    def extract_text_file(self, file_path: str) -> List[Document]:
        """
        提取文本文件内容

        Args:
            file_path: 文件路径

        Returns:
            文档列表
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return [Document(page_content=content, metadata={"source": file_path})]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        分割文档为小块

        Args:
            documents: 文档列表

        Returns:
            分割后的文档块列表
        """
        doc_splits = self.text_splitter.split_documents(documents)
        return doc_splits

    def get_vector_store(self) -> Milvus:
        """
        获取向量存储实例

        Returns:
            Milvus向量存储
        """
        vector_store = Milvus(
            embedding_function=self.embedding,
            connection_args={"uri": MILVUS_URI},
            collection_name=MILVUS_COLLECTION_NAME,
            index_params={"index_type": "FLAT", "metric_type": "L2"},
        )
        return vector_store

    def add_documents_to_vector_store(self, doc_splits: List[Document]) -> List[str]:
        """
        将文档块添加到向量数据库

        Args:
            doc_splits: 文档块列表

        Returns:
            向量ID列表
        """
        vector_store = self.get_vector_store()
        ids = vector_store.add_documents(documents=doc_splits)
        return ids

    def process_document(
        self, file_path: str, file_type: str
    ) -> tuple[List[Document], List[str]]:
        """
        处理文档的完整流程

        Args:
            file_path: 文件路径
            file_type: 文件类型

        Returns:
            (文档块列表, 向量ID列表)
        """
        # 1. 提取文本
        if file_type == ".pdf":
            documents = self.extract_pdf_text(file_path)
        else:
            documents = self.extract_text_file(file_path)

        # 2. 分块
        doc_splits = self.split_documents(documents)

        # 3. 向量化并存储
        vector_ids = self.add_documents_to_vector_store(doc_splits)

        return doc_splits, vector_ids
