#!/usr/bin/env python3
"""
图片分析服务 - 迁移自examples/image_analyzer.py
使用大模型对marker提取的图片进行分析和描述
"""

import base64
import io
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from backend.conf.config import settings

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI库未安装，图片分析功能将不可用")

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL库未安装，图片处理功能将受限")


class ImageAnalyzer:
    """图片分析器，使用大模型分析图片内容"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o",
        default_prompt: str = "请详细描述这张图片的内容，包括文字、图表、数据等所有可见信息。",
    ):
        """
        初始化图片分析器

        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL
            model: 使用的模型名称
            default_prompt: 默认的分析提示词
        """
        self.api_key = (
            api_key
            or settings.ui_tars_model.api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("QWEN_API_KEY")
        )
        self.base_url = (
            base_url
            or settings.ui_tars_model.base_url
            or os.getenv("OPENAI_API_BASE")
            or os.getenv("QWEN_API_BASE")
        )
        self.model = settings.ui_tars_model.model or model
        self.default_prompt = default_prompt

        # 检查是否有可用的API密钥
        if not self.api_key:
            logger.warning("⚠️ 未找到API密钥，图片分析功能将不可用")
            self.client = None
        else:
            try:
                if OPENAI_AVAILABLE:
                    self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                    logger.info(f"✅ 图片分析器初始化成功，使用模型: {self.model}")
                else:
                    self.client = None
                    logger.error("❌ OpenAI库未安装，无法创建客户端")
            except Exception as e:
                logger.error(f"❌ 图片分析器初始化失败: {e}")
                self.client = None

    def is_available(self) -> bool:
        """检查图片分析功能是否可用"""
        return self.client is not None and OPENAI_AVAILABLE

    def _image_to_base64(self, image_data: Any) -> Optional[str]:
        """
        将图片数据转换为base64编码

        Args:
            image_data: 图片数据，可以是bytes、PIL Image或其他格式

        Returns:
            base64编码的图片字符串，如果转换失败返回None
        """
        try:
            if isinstance(image_data, bytes):
                # 直接是字节数据
                return base64.b64encode(image_data).decode("utf-8")

            elif hasattr(image_data, "save") and PIL_AVAILABLE:
                # PIL Image对象
                buffer = io.BytesIO()
                # 确保图片格式为RGB
                if image_data.mode != "RGB":
                    image_data = image_data.convert("RGB")
                image_data.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode("utf-8")

            elif hasattr(image_data, "tobytes"):
                # 有tobytes方法的图片对象
                return base64.b64encode(image_data.tobytes()).decode("utf-8")

            else:
                logger.warning(f"⚠️ 不支持的图片数据类型: {type(image_data)}")
                return None

        except Exception as e:
            logger.error(f"❌ 图片转换为base64失败: {e}")
            return None

    async def analyze_image(
        self, image_data: Any, prompt: Optional[str] = None, image_name: str = "image"
    ) -> Dict[str, Any]:
        """
        分析单张图片

        Args:
            image_data: 图片数据
            prompt: 分析提示词，如果为None则使用默认提示词
            image_name: 图片名称，用于日志记录

        Returns:
            包含分析结果的字典
        """
        logger.info(f"🔍 开始分析图片: {image_name}")

        if not self.is_available():
            logger.error("❌ 图片分析功能不可用")
            return {
                "success": False,
                "error": "图片分析功能不可用，请检查API配置",
                "image_name": image_name,
            }

        # 转换图片为base64
        base64_image = self._image_to_base64(image_data)
        if not base64_image:
            logger.error(f"❌ 图片 {image_name} 转换失败")
            return {
                "success": False,
                "error": "图片格式转换失败",
                "image_name": image_name,
            }

        # 使用的提示词
        analysis_prompt = prompt or self.default_prompt

        try:
            logger.debug(f"🤖 调用大模型分析图片: {image_name}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )

            description = response.choices[0].message.content

            logger.success(f"✅ 图片 {image_name} 分析完成")
            logger.debug(f"   📝 分析结果长度: {len(description)} 字符")

            return {
                "success": True,
                "description": description,
                "image_name": image_name,
                "model": self.model,
                "prompt": analysis_prompt,
                "tokens_used": (
                    response.usage.total_tokens if hasattr(response, "usage") else None
                ),
            }

        except Exception as e:
            logger.error(f"❌ 图片 {image_name} 分析失败: {e}")
            return {"success": False, "error": str(e), "image_name": image_name}

    async def analyze_images_batch(
        self, images: Dict[str, Any], prompt: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量分析图片

        Args:
            images: 图片字典，键为图片名称，值为图片数据
            prompt: 分析提示词

        Returns:
            分析结果字典，键为图片名称，值为分析结果
        """
        logger.info(f"🔍 开始批量分析图片，共 {len(images)} 张")

        results = {}

        for image_name, image_data in images.items():
            result = await self.analyze_image(image_data, prompt, image_name)
            results[image_name] = result

        # 统计结果
        success_count = sum(1 for r in results.values() if r.get("success", False))
        logger.info(f"📊 批量分析完成: {success_count}/{len(images)} 张成功")

        return results

    def replace_images_with_descriptions(
        self, text: str, image_descriptions: Dict[str, str]
    ) -> str:
        """
        将文本中的图片引用替换为图片描述

        Args:
            text: 原始文本
            image_descriptions: 图片描述字典，键为图片名称，值为描述

        Returns:
            替换后的文本
        """
        logger.debug(
            f"🔄 开始替换文本中的图片引用，共 {len(image_descriptions)} 个描述"
        )

        modified_text = text
        replacements_made = 0

        for image_name, description in image_descriptions.items():
            # 查找图片引用模式，使用更灵活的匹配
            import re

            # 创建正则表达式模式来匹配各种图片引用格式
            patterns = [
                rf"!\[([^\]]*)\]\({re.escape(image_name)}\)",  # ![任意文本](image_name)
                rf"!\[\]\({re.escape(image_name)}\)",  # ![](image_name)
            ]

            for pattern in patterns:
                matches = list(re.finditer(pattern, modified_text))
                for match in reversed(matches):  # 从后往前替换，避免位置偏移
                    # 替换为描述
                    replacement = f"\n\n**图片描述 ({image_name})**: {description}\n\n"
                    modified_text = (
                        modified_text[: match.start()]
                        + replacement
                        + modified_text[match.end() :]
                    )
                    replacements_made += 1
                    logger.debug(f"   ✅ 替换图片引用: {match.group()}")

        logger.debug(f"✅ 图片引用替换完成，共替换 {replacements_made} 处")
        return modified_text


# 创建默认的图片分析器实例
def create_default_analyzer() -> ImageAnalyzer:
    """创建默认配置的图片分析器"""
    # 优先使用通义千问配置
    qwen_key = os.getenv("QWEN_API_KEY")
    if qwen_key:
        return ImageAnalyzer(
            api_key=settings.qwen_model.api_key,
            base_url=settings.qwen_model.base_url,
            model=settings.qwen_model.model,
            default_prompt="请详细描述这张图片的内容，包括文字、图表、数据等所有可见信息。如果图片包含表格或数据，请尽可能准确地描述其内容。",
        )

    # 回退到OpenAI配置
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return ImageAnalyzer(
            api_key=openai_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model="gpt-4o",
            default_prompt="Please describe this image in detail, including any text, charts, data, or other visible information. If the image contains tables or data, please describe their content as accurately as possible.",
        )

    # 没有可用的API密钥
    logger.warning("⚠️ 未找到可用的API密钥，创建不可用的图片分析器")
    return ImageAnalyzer()


# 默认分析器实例
default_analyzer = create_default_analyzer()
