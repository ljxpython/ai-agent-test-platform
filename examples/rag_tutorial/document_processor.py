"""
文档处理器
负责文档加载、分块、预处理等功能
"""

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

# 文档处理相关导入
try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2未安装，无法处理PDF文件")

try:
    from docx import Document as DocxDocument

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx未安装，无法处理DOCX文件")


@dataclass
class DocumentChunk:
    """文档块数据结构"""

    text: str
    metadata: Dict[str, Any]
    chunk_id: str
    source: str
    start_pos: int = 0
    end_pos: int = 0


class DocumentProcessor:
    """文档处理器"""

    def __init__(self, config=None):
        # from .config import get_config
        from examples.rag_tutorial.config import get_config

        self.config = config or get_config().document

    def load_document(self, file_path: str) -> str:
        """加载文档内容"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_ext = file_path.suffix.lower()

        if file_ext not in self.config.supported_formats:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        logger.info(f"加载文档: {file_path}")

        try:
            if file_ext == ".txt":
                return self._load_text_file(file_path)
            elif file_ext == ".md":
                return self._load_markdown_file(file_path)
            elif file_ext == ".pdf":
                return self._load_pdf_file(file_path)
            elif file_ext == ".docx":
                return self._load_docx_file(file_path)
            else:
                raise ValueError(f"未实现的文件格式处理: {file_ext}")

        except Exception as e:
            logger.error(f"加载文档失败: {e}")
            raise

    def _load_text_file(self, file_path: Path) -> str:
        """加载文本文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_markdown_file(self, file_path: Path) -> str:
        """加载Markdown文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 简单的Markdown预处理
        # 移除代码块
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        # 移除行内代码
        content = re.sub(r"`[^`]+`", "", content)
        # 移除链接但保留文本
        content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)
        # 移除图片
        content = re.sub(r"!\[.*?\]\([^\)]+\)", "", content)

        return content

    def _load_pdf_file(self, file_path: Path) -> str:
        """加载PDF文件"""
        if not PDF_AVAILABLE:
            raise ImportError("需要安装PyPDF2来处理PDF文件: pip install PyPDF2")

        text = ""
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)

            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text += f"\n--- 第{page_num + 1}页 ---\n"
                        text += page_text
                except Exception as e:
                    logger.warning(f"提取第{page_num + 1}页内容失败: {e}")

        return text

    def _load_docx_file(self, file_path: Path) -> str:
        """加载DOCX文件"""
        if not DOCX_AVAILABLE:
            raise ImportError(
                "需要安装python-docx来处理DOCX文件: pip install python-docx"
            )

        doc = DocxDocument(file_path)
        text = ""

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"

        return text

    def split_text_into_chunks(
        self, text: str, source: str = ""
    ) -> List[DocumentChunk]:
        """将文本分割成块"""
        if not text.strip():
            return []

        logger.info(f"开始分割文本，长度: {len(text)}")

        # 清理文本
        text = self._clean_text(text)

        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        # 按段落分割
        paragraphs = self._split_by_paragraphs(text)

        current_chunk = ""
        current_pos = 0

        for paragraph in paragraphs:
            # 如果当前块加上新段落超过大小限制
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                # 保存当前块
                chunk = self._create_chunk(
                    current_chunk, source, len(chunks), current_pos
                )
                chunks.append(chunk)

                # 开始新块，保留重叠部分
                if overlap > 0:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + paragraph
                else:
                    current_chunk = paragraph

                current_pos += len(current_chunk) - overlap
            else:
                current_chunk += paragraph

        # 处理最后一个块
        if current_chunk.strip():
            chunk = self._create_chunk(current_chunk, source, len(chunks), current_pos)
            chunks.append(chunk)

        # 限制块数量
        if len(chunks) > self.config.max_chunks_per_doc:
            logger.warning(
                f"文档块数量 {len(chunks)} 超过限制 {self.config.max_chunks_per_doc}，将截断"
            )
            chunks = chunks[: self.config.max_chunks_per_doc]

        logger.info(f"文本分割完成，生成 {len(chunks)} 个块")
        return chunks

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空白字符
        text = re.sub(r"\s+", " ", text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()[\]{}"\'-]', "", text)
        # 移除过短的行
        lines = text.split("\n")
        lines = [line.strip() for line in lines if len(line.strip()) > 10]

        return "\n".join(lines)

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 按双换行符分割段落
        paragraphs = re.split(r"\n\s*\n", text)

        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # 如果段落太长，进一步分割
        final_paragraphs = []
        for paragraph in paragraphs:
            if len(paragraph) > self.config.chunk_size:
                # 按句子分割
                sentences = re.split(r"[.!?。！？]", paragraph)
                current_para = ""

                for sentence in sentences:
                    if len(current_para) + len(sentence) > self.config.chunk_size:
                        if current_para:
                            final_paragraphs.append(current_para.strip())
                        current_para = sentence
                    else:
                        current_para += sentence + "。"

                if current_para:
                    final_paragraphs.append(current_para.strip())
            else:
                final_paragraphs.append(paragraph)

        return final_paragraphs

    def _create_chunk(
        self, text: str, source: str, chunk_index: int, start_pos: int
    ) -> DocumentChunk:
        """创建文档块"""
        # 生成块ID
        chunk_id = self._generate_chunk_id(text, source, chunk_index)

        # 创建元数据
        metadata = {
            "source": source,
            "chunk_index": chunk_index,
            "chunk_size": len(text),
            "word_count": len(text.split()),
            "language": self._detect_language(text),
        }

        return DocumentChunk(
            text=text.strip(),
            metadata=metadata,
            chunk_id=chunk_id,
            source=source,
            start_pos=start_pos,
            end_pos=start_pos + len(text),
        )

    def _generate_chunk_id(self, text: str, source: str, chunk_index: int) -> str:
        """生成块ID"""
        content = f"{source}_{chunk_index}_{text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()

    def _detect_language(self, text: str) -> str:
        """简单的语言检测"""
        # 统计中文字符
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        total_chars = len(text)

        if chinese_chars / total_chars > 0.3:
            return "zh"
        else:
            return "en"

    def process_directory(self, directory_path: str) -> List[DocumentChunk]:
        """处理目录中的所有文档"""
        directory_path = Path(directory_path)

        if not directory_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory_path}")

        all_chunks = []

        # 遍历目录
        for file_path in directory_path.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.config.supported_formats
            ):
                try:
                    logger.info(f"处理文件: {file_path}")

                    # 加载文档
                    content = self.load_document(str(file_path))

                    # 分割成块
                    chunks = self.split_text_into_chunks(content, str(file_path))
                    all_chunks.extend(chunks)

                    logger.info(f"文件 {file_path} 处理完成，生成 {len(chunks)} 个块")

                except Exception as e:
                    logger.error(f"处理文件 {file_path} 失败: {e}")
                    continue

        logger.info(f"目录处理完成，总共生成 {len(all_chunks)} 个文档块")
        return all_chunks


# 便捷函数
def process_single_file(file_path: str) -> List[DocumentChunk]:
    """处理单个文件"""
    processor = DocumentProcessor()
    content = processor.load_document(file_path)
    return processor.split_text_into_chunks(content, file_path)


def process_text_directly(
    text: str, source: str = "direct_input"
) -> List[DocumentChunk]:
    """直接处理文本"""
    processor = DocumentProcessor()
    return processor.split_text_into_chunks(text, source)


if __name__ == "__main__":
    # 测试代码
    processor = DocumentProcessor()

    # 测试文本分割
    test_text = """
    这是第一段文本。它包含了一些基本信息。

    这是第二段文本。它提供了更多的详细信息。
    这段文本比较长，可能需要进一步分割。

    这是第三段文本。它是最后一段。
    """

    chunks = processor.split_text_into_chunks(test_text, "test.txt")

    print(f"生成了 {len(chunks)} 个文档块:")
    for i, chunk in enumerate(chunks):
        print(f"块 {i + 1}:")
        print(f"  文本: {chunk.text[:100]}...")
        print(f"  元数据: {chunk.metadata}")
        print(f"  块ID: {chunk.chunk_id}")
        print()
