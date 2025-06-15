"""
文件提取器配置 - 迁移自examples/conf/file_extractor_config.py
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.conf.config import settings


@dataclass
class MarkerConfig:
    """Marker配置类"""

    # 输出格式配置
    output_format: str = "markdown"  # markdown, json, html
    output_dir: str = "output"

    # LLM配置
    use_llm: bool = False
    llm_service: str = "marker.services.openai.OpenAIService"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = ""

    # 阿里云通义千问配置
    qwen_base_url: str = settings.qwen_model.base_url
    qwen_model: str = settings.qwen_model.model
    qwen_api_key: str = settings.qwen_model.api_key

    # 处理配置
    disable_image_extraction: bool = True  # 启用图片描述功能时设为True
    force_ocr: bool = False
    format_lines: bool = True
    strip_existing_ocr: bool = False
    redo_inline_math: bool = False

    # 图片描述配置
    enable_image_description: bool = True  # 是否启用图片描述功能
    image_description_prompt: str = (
        "请详细描述这张图片的内容，包括文字、图表、数据等所有可见信息。"
    )

    # 页面范围配置
    page_range: Optional[str] = None
    paginate_output: bool = False

    # 调试配置
    debug: bool = False

    # 文件大小限制 (50MB)
    max_file_size: int = 50 * 1024 * 1024

    # 支持的文件类型
    supported_extensions: tuple = (
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".bmp",
        ".gif",
        ".pptx",
        ".ppt",
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".html",
        ".htm",
        ".epub",
        ".txt",
        ".md",  # 添加TXT支持
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        config_dict = {
            "output_format": self.output_format,
            "output_dir": self.output_dir,
            "use_llm": self.use_llm,
            "disable_image_extraction": self.disable_image_extraction,
            "force_ocr": self.force_ocr,
            "format_lines": self.format_lines,
            "strip_existing_ocr": self.strip_existing_ocr,
            "redo_inline_math": self.redo_inline_math,
            "debug": self.debug,
        }

        # 添加LLM服务配置
        if self.use_llm:
            config_dict.update(
                {
                    "llm_service": self.llm_service,
                }
            )

            # 根据不同的LLM服务添加相应配置
            if "openai" in self.llm_service.lower():
                if self.qwen_api_key:  # 使用通义千问
                    config_dict.update(
                        {
                            "openai_base_url": self.qwen_base_url,
                            "openai_model": self.qwen_model,
                            "openai_api_key": self.qwen_api_key,
                        }
                    )
                else:  # 使用OpenAI
                    config_dict.update(
                        {
                            "openai_base_url": self.openai_base_url,
                            "openai_model": self.openai_model,
                            "openai_api_key": self.openai_api_key,
                        }
                    )

        # 图片描述功能配置
        if self.enable_image_description and self.use_llm:
            config_dict["disable_image_extraction"] = (
                True  # 启用图片描述时必须禁用图片提取
            )

        # 添加页面范围配置
        if self.page_range:
            config_dict["page_range"] = self.page_range

        if self.paginate_output:
            config_dict["paginate_output"] = self.paginate_output

        return config_dict

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "MarkerConfig":
        """从字典创建配置对象"""
        return cls(**{k: v for k, v in config_dict.items() if hasattr(cls, k)})

    def validate(self) -> bool:
        """验证配置是否有效"""
        if self.use_llm and not (self.openai_api_key or self.qwen_api_key):
            raise ValueError("使用LLM时必须提供API密钥")

        if self.output_format not in ["markdown", "json", "html"]:
            raise ValueError("输出格式必须是 markdown, json 或 html")

        if self.max_file_size <= 0:
            raise ValueError("文件大小限制必须大于0")

        return True


class ConfigManager:
    """配置管理器"""

    def __init__(self, config: Optional[MarkerConfig] = None):
        self.config = config or MarkerConfig()

    def update_config(self, **kwargs) -> None:
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"未知的配置项: {key}")

    def get_config_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        return self.config.to_dict()

    def validate_config(self) -> bool:
        """验证配置"""
        return self.config.validate()

    def is_file_supported(self, filename: str) -> bool:
        """检查文件是否支持"""
        from pathlib import Path

        extension = Path(filename).suffix.lower()
        return extension in self.config.supported_extensions

    def get_supported_extensions(self) -> tuple:
        """获取支持的文件扩展名"""
        return self.config.supported_extensions


# 默认配置实例
default_config = MarkerConfig()
default_config_manager = ConfigManager(default_config)


@dataclass
class MarkdownContent:
    """Markdown内容数据类"""

    text: str
    images: Dict[str, Any]
    metadata: Dict[str, Any]
    tables: List[str]
    headers: List[str]
    links: List[str]
    code_blocks: List[str]
    math_expressions: List[str]


class MarkdownExtractor:
    """Markdown文本提取器"""

    def __init__(self):
        # 正则表达式模式
        self.patterns = {
            "headers": re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE),
            "links": re.compile(r"\[([^\]]+)\]\(([^)]+)\)"),
            "images": re.compile(r"!\[([^\]]*)\]\(([^)]+)\)"),
            "code_blocks": re.compile(r"```[\s\S]*?```", re.MULTILINE),
            "inline_code": re.compile(r"`([^`]+)`"),
            "math_blocks": re.compile(r"\$\$[\s\S]*?\$\$", re.MULTILINE),
            "inline_math": re.compile(r"\$([^$]+)\$"),
            "tables": re.compile(r"^\|.*\|$", re.MULTILINE),
            "bold": re.compile(r"\*\*([^*]+)\*\*"),
            "italic": re.compile(r"\*([^*]+)\*"),
            "strikethrough": re.compile(r"~~([^~]+)~~"),
        }

    def extract_from_rendered(self, rendered_result: Any) -> MarkdownContent:
        """从marker渲染结果中提取markdown内容"""
        try:
            # 处理不同类型的渲染结果
            if hasattr(rendered_result, "markdown"):
                # 标准markdown输出
                text = rendered_result.markdown
                images = getattr(rendered_result, "images", {})
                metadata = getattr(rendered_result, "metadata", {})
            elif hasattr(rendered_result, "children"):
                # JSON格式输出
                text, images, metadata = self._extract_from_json(rendered_result)
            else:
                # 字符串格式
                text = str(rendered_result)
                images = {}
                metadata = {}

            return self._analyze_markdown_content(text, images, metadata)

        except Exception as e:
            raise Exception(f"提取markdown内容失败: {str(e)}")

    def _extract_from_json(self, json_result: Any) -> Tuple[str, Dict, Dict]:
        """从JSON格式结果中提取内容"""
        text_parts = []
        images = {}
        metadata = getattr(json_result, "metadata", {})

        def extract_text_recursive(block):
            if hasattr(block, "children") and block.children:
                for child in block.children:
                    extract_text_recursive(child)

            # 提取文本内容
            if hasattr(block, "html"):
                # 从HTML中提取纯文本
                html_content = block.html
                # 简单的HTML到文本转换
                text_content = re.sub(r"<[^>]+>", "", html_content)
                if text_content.strip():
                    text_parts.append(text_content.strip())

            # 提取图片
            if hasattr(block, "images") and block.images:
                images.update(block.images)

        if hasattr(json_result, "children"):
            for page in (
                json_result.children
                if isinstance(json_result.children, list)
                else [json_result]
            ):
                extract_text_recursive(page)

        return "\n\n".join(text_parts), images, metadata

    def _analyze_markdown_content(
        self, text: str, images: Dict, metadata: Dict
    ) -> MarkdownContent:
        """分析markdown内容，提取各种元素"""

        # 提取标题
        headers = [match.group(1) for match in self.patterns["headers"].finditer(text)]

        # 提取链接
        links = [match.group(2) for match in self.patterns["links"].finditer(text)]

        # 提取代码块
        code_blocks = [
            match.group(0) for match in self.patterns["code_blocks"].finditer(text)
        ]

        # 提取数学表达式
        math_blocks = [
            match.group(0) for match in self.patterns["math_blocks"].finditer(text)
        ]
        inline_math = [
            match.group(1) for match in self.patterns["inline_math"].finditer(text)
        ]
        math_expressions = math_blocks + inline_math

        # 提取表格
        tables = self._extract_tables(text)

        return MarkdownContent(
            text=text,
            images=images,
            metadata=metadata,
            tables=tables,
            headers=headers,
            links=links,
            code_blocks=code_blocks,
            math_expressions=math_expressions,
        )

    def _extract_tables(self, text: str) -> List[str]:
        """提取表格内容"""
        tables = []
        lines = text.split("\n")
        current_table = []
        in_table = False

        for line in lines:
            if self.patterns["tables"].match(line):
                if not in_table:
                    in_table = True
                    current_table = [line]
                else:
                    current_table.append(line)
            else:
                if in_table:
                    # 表格结束
                    if current_table:
                        tables.append("\n".join(current_table))
                    current_table = []
                    in_table = False

        # 处理最后一个表格
        if current_table:
            tables.append("\n".join(current_table))

        return tables

    def get_plain_text(self, markdown_content: MarkdownContent) -> str:
        """获取纯文本内容（去除markdown格式）"""
        text = markdown_content.text

        # 移除代码块
        text = self.patterns["code_blocks"].sub("", text)

        # 移除数学表达式
        text = self.patterns["math_blocks"].sub("", text)
        text = self.patterns["inline_math"].sub(r"\1", text)

        # 移除图片
        text = self.patterns["images"].sub("", text)

        # 移除链接格式，保留文本
        text = self.patterns["links"].sub(r"\1", text)

        # 移除格式标记
        text = self.patterns["bold"].sub(r"\1", text)
        text = self.patterns["italic"].sub(r"\1", text)
        text = self.patterns["strikethrough"].sub(r"\1", text)
        text = self.patterns["inline_code"].sub(r"\1", text)

        # 移除标题标记
        text = self.patterns["headers"].sub(r"\1", text)

        # 清理多余的空行
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        return text

    def get_structured_content(
        self, markdown_content: MarkdownContent
    ) -> Dict[str, Any]:
        """获取结构化内容"""
        return {
            "full_text": markdown_content.text,
            "plain_text": self.get_plain_text(markdown_content),
            "headers": markdown_content.headers,
            "tables": markdown_content.tables,
            "links": markdown_content.links,
            "code_blocks": markdown_content.code_blocks,
            "math_expressions": markdown_content.math_expressions,
            "images": markdown_content.images,
            "metadata": markdown_content.metadata,
            "statistics": {
                "total_characters": len(markdown_content.text),
                "total_words": len(markdown_content.text.split()),
                "headers_count": len(markdown_content.headers),
                "tables_count": len(markdown_content.tables),
                "links_count": len(markdown_content.links),
                "code_blocks_count": len(markdown_content.code_blocks),
                "math_expressions_count": len(markdown_content.math_expressions),
                "images_count": len(markdown_content.images),
            },
        }
