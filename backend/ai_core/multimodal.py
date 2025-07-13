"""
多模态消息处理模块
提供通用的多模态消息创建和处理功能，支持文本、图片等多种内容类型
"""

import base64
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import PIL.Image
from autogen_agentchat.messages import MultiModalMessage, TextMessage
from autogen_core import Image
from loguru import logger


class MultiModalProcessor:
    """多模态消息处理器"""

    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".webp",
        ".tiff",
        ".tif",
    }

    # 图片大小限制 (10MB)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024

    def __init__(self):
        """初始化多模态处理器"""
        logger.info("🖼️ [多模态处理器] 初始化完成")

    @classmethod
    def load_image_from_file(cls, file_path: Union[str, Path]) -> Image:
        """
        从本地文件加载图片

        Args:
            file_path: 图片文件路径

        Returns:
            Image: AutoGen Image对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或加载失败
        """
        try:
            file_path = Path(file_path)
            logger.debug(f"🔍 [图片加载] 开始加载图片: {file_path}")

            # 检查文件是否存在
            if not file_path.exists():
                error_msg = f"图片文件不存在: {file_path}"
                logger.error(f"❌ [图片加载] {error_msg}")
                raise FileNotFoundError(error_msg)

            # 检查文件格式
            if file_path.suffix.lower() not in cls.SUPPORTED_IMAGE_FORMATS:
                error_msg = f"不支持的图片格式: {file_path.suffix}，支持的格式: {cls.SUPPORTED_IMAGE_FORMATS}"
                logger.error(f"❌ [图片加载] {error_msg}")
                raise ValueError(error_msg)

            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size > cls.MAX_IMAGE_SIZE:
                error_msg = f"图片文件过大: {file_size / 1024 / 1024:.2f}MB，最大支持: {cls.MAX_IMAGE_SIZE / 1024 / 1024}MB"
                logger.error(f"❌ [图片加载] {error_msg}")
                raise ValueError(error_msg)

            # 加载图片
            pil_image = PIL.Image.open(file_path)

            # 验证图片是否有效
            pil_image.verify()

            # 重新打开图片（verify会关闭文件）
            pil_image = PIL.Image.open(file_path)

            # 转换为RGB模式（如果需要）
            if pil_image.mode not in ("RGB", "RGBA"):
                logger.debug(f"🔄 [图片加载] 转换图片模式: {pil_image.mode} → RGB")
                pil_image = pil_image.convert("RGB")

            image = Image(pil_image)

            logger.success(
                f"✅ [图片加载] 图片加载成功: {file_path.name} ({file_size / 1024:.1f}KB, {pil_image.size})"
            )
            return image

        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            error_msg = f"无法从文件加载图片 {file_path}: {str(e)}"
            logger.error(f"❌ [图片加载] {error_msg}")
            raise ValueError(error_msg)

    @classmethod
    def load_image_from_bytes(
        cls, image_bytes: bytes, filename: str = "image"
    ) -> Image:
        """
        从字节数据加载图片

        Args:
            image_bytes: 图片字节数据
            filename: 文件名（用于日志）

        Returns:
            Image: AutoGen Image对象

        Raises:
            ValueError: 图片数据无效或加载失败
        """
        try:
            logger.debug(
                f"🔍 [图片加载] 从字节数据加载图片: {filename} ({len(image_bytes)} bytes)"
            )

            # 检查数据大小
            if len(image_bytes) > cls.MAX_IMAGE_SIZE:
                error_msg = f"图片数据过大: {len(image_bytes) / 1024 / 1024:.2f}MB，最大支持: {cls.MAX_IMAGE_SIZE / 1024 / 1024}MB"
                logger.error(f"❌ [图片加载] {error_msg}")
                raise ValueError(error_msg)

            # 从字节数据创建PIL图片
            image_io = io.BytesIO(image_bytes)
            pil_image = PIL.Image.open(image_io)

            # 验证图片
            pil_image.verify()

            # 重新打开图片
            image_io.seek(0)
            pil_image = PIL.Image.open(image_io)

            # 转换为RGB模式（如果需要）
            if pil_image.mode not in ("RGB", "RGBA"):
                logger.debug(f"🔄 [图片加载] 转换图片模式: {pil_image.mode} → RGB")
                pil_image = pil_image.convert("RGB")

            image = Image(pil_image)

            logger.success(
                f"✅ [图片加载] 从字节数据加载图片成功: {filename} ({len(image_bytes) / 1024:.1f}KB, {pil_image.size})"
            )
            return image

        except Exception as e:
            error_msg = f"无法从字节数据加载图片 {filename}: {str(e)}"
            logger.error(f"❌ [图片加载] {error_msg}")
            raise ValueError(error_msg)

    @classmethod
    def load_image_from_base64(cls, base64_data: str, filename: str = "image") -> Image:
        """
        从Base64字符串加载图片

        Args:
            base64_data: Base64编码的图片数据
            filename: 文件名（用于日志）

        Returns:
            Image: AutoGen Image对象

        Raises:
            ValueError: Base64数据无效或图片加载失败
        """
        try:
            logger.debug(f"🔍 [图片加载] 从Base64数据加载图片: {filename}")

            # 解码Base64数据
            try:
                # 处理data URL格式 (data:image/png;base64,...)
                if base64_data.startswith("data:"):
                    base64_data = base64_data.split(",", 1)[1]

                image_bytes = base64.b64decode(base64_data)
            except Exception as e:
                error_msg = f"Base64数据解码失败: {str(e)}"
                logger.error(f"❌ [图片加载] {error_msg}")
                raise ValueError(error_msg)

            return cls.load_image_from_bytes(image_bytes, filename)

        except ValueError:
            raise
        except Exception as e:
            error_msg = f"无法从Base64数据加载图片 {filename}: {str(e)}"
            logger.error(f"❌ [图片加载] {error_msg}")
            raise ValueError(error_msg)

    @classmethod
    def create_multimodal_message(
        cls,
        text: str,
        images: Optional[List[Union[str, Path, Image, bytes, Dict[str, Any]]]] = None,
        source: str = "user",
    ) -> MultiModalMessage:
        """
        创建多模态消息

        Args:
            text: 文本内容
            images: 图片列表，支持多种格式：
                   - str/Path: 文件路径
                   - Image: AutoGen Image对象
                   - bytes: 图片字节数据
                   - Dict: {"type": "file|bytes|base64", "data": ..., "filename": ...}
            source: 消息来源

        Returns:
            MultiModalMessage: 多模态消息对象

        Raises:
            ValueError: 图片加载失败
        """
        try:
            logger.info(
                f"🔨 [多模态消息] 创建多模态消息，文本长度: {len(text)}, 图片数量: {len(images) if images else 0}"
            )

            content = [text]

            if images:
                for i, img in enumerate(images):
                    try:
                        logger.debug(f"🖼️ [多模态消息] 处理第 {i+1} 张图片: {type(img)}")

                        if isinstance(img, Image):
                            # 已经是AutoGen Image对象
                            content.append(img)
                            logger.debug(
                                f"✅ [多模态消息] 第 {i+1} 张图片: 直接使用Image对象"
                            )

                        elif isinstance(img, (str, Path)):
                            # 文件路径
                            image = cls.load_image_from_file(img)
                            content.append(image)

                        elif isinstance(img, bytes):
                            # 字节数据
                            image = cls.load_image_from_bytes(img, f"image_{i+1}")
                            content.append(image)

                        elif isinstance(img, dict):
                            # 字典格式
                            img_type = img.get("type", "file")
                            img_data = img.get("data")
                            img_filename = img.get("filename", f"image_{i+1}")

                            if img_type == "file":
                                image = cls.load_image_from_file(img_data)
                            elif img_type == "bytes":
                                image = cls.load_image_from_bytes(
                                    img_data, img_filename
                                )
                            elif img_type == "base64":
                                image = cls.load_image_from_base64(
                                    img_data, img_filename
                                )
                            else:
                                raise ValueError(f"不支持的图片类型: {img_type}")

                            content.append(image)

                        else:
                            # 尝试作为文件路径处理
                            image = cls.load_image_from_file(str(img))
                            content.append(image)

                    except Exception as e:
                        error_msg = f"处理第 {i+1} 张图片失败: {str(e)}"
                        logger.error(f"❌ [多模态消息] {error_msg}")
                        raise ValueError(error_msg)

            message = MultiModalMessage(content=content, source=source)

            logger.success(
                f"✅ [多模态消息] 多模态消息创建成功，内容项数: {len(content)}"
            )
            return message

        except Exception as e:
            error_msg = f"创建多模态消息失败: {str(e)}"
            logger.error(f"❌ [多模态消息] {error_msg}")
            raise ValueError(error_msg)

    @classmethod
    def create_text_message(cls, text: str, source: str = "user") -> TextMessage:
        """
        创建文本消息

        Args:
            text: 文本内容
            source: 消息来源

        Returns:
            TextMessage: 文本消息对象
        """
        logger.debug(f"📝 [文本消息] 创建文本消息，长度: {len(text)}")
        return TextMessage(content=text, source=source)


# 创建全局实例
multimodal_processor = MultiModalProcessor()

# 导出便捷函数
load_image_from_file = multimodal_processor.load_image_from_file
load_image_from_bytes = multimodal_processor.load_image_from_bytes
load_image_from_base64 = multimodal_processor.load_image_from_base64
create_multimodal_message = multimodal_processor.create_multimodal_message
create_text_message = multimodal_processor.create_text_message
