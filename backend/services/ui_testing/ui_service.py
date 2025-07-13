"""
UI测试服务
基于AI核心框架重构的UI测试服务实现
"""

import asyncio
import hashlib
import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

# 使用AI核心框架
from backend.ai_core.llm import validate_model_configs
from backend.ai_core.memory import get_memory_manager
from backend.ai_core.message_queue import (
    get_streaming_sse_messages_from_queue,
    put_message_to_queue,
)

# 控制器
from backend.controllers.project_controller import project_controller

# 数据库模型
from backend.models.rag import RAGCollection
from backend.models.rag_file import RAGFileRecord
from backend.models.ui_task import TaskStatus, TaskType, UITask

# 服务
from backend.services.rag.rag_service import get_rag_service
from backend.services.ui_testing.ui_runtime import get_ui_testing_runtime


class UITestingService:
    """UI测试服务 - 基于AI核心框架重构版本"""

    def __init__(self):
        """初始化服务"""
        self.runtime = get_ui_testing_runtime()
        self.memory_manager = get_memory_manager()
        self.supported_image_formats = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
        }

        logger.info("🎯 [UI测试服务] 基于AI核心框架的服务初始化完成")

    def _sanitize_collection_name(self, name: str) -> str:
        """
        清理Collection名称，确保符合Milvus命名规则
        Milvus只允许数字、字母和下划线
        """
        # 将连字符替换为下划线
        sanitized = name.replace("-", "_")
        # 移除其他特殊字符，只保留字母、数字和下划线
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", sanitized)
        # 确保不以数字开头
        if sanitized and sanitized[0].isdigit():
            sanitized = f"c_{sanitized}"
        return sanitized

    async def process_image_upload(
        self,
        project: str,
        image_files: List[dict],
        conversation_id: str,
        user_requirement: str = "",
    ) -> Dict[str, Any]:
        """
        处理图片上传（业务前置处理，不使用流式输出）

        Args:
            project: 项目名称
            image_files: 图片文件数据列表
            conversation_id: 对话ID
            user_requirement: 用户需求

        Returns:
            处理结果统计
        """
        logger.info(f"📷 [UI测试服务] 开始处理图片上传 | 对话ID: {conversation_id}")
        logger.info(f"🏗️ 项目: {project} | 图片数量: {len(image_files)}")

        try:
            # 统计结果
            result = {
                "processed_count": 0,
                "failed_count": 0,
                "duplicate_count": 0,
                "tasks": [],
            }

            # 1. 检查项目是否存在，不存在则创建
            await self._ensure_project_exists(project, conversation_id)

            # 2. 检查并创建Collection
            collection_info = await self._ensure_collections_exist(
                project, conversation_id
            )

            # 3. 处理每个图片文件
            for i, image_file_data in enumerate(image_files):
                try:
                    # 创建任务记录
                    task_id = f"upload_{uuid.uuid4().hex[:8]}"
                    filename = image_file_data.get("filename", f"image_{i+1}")
                    file_content = image_file_data.get("content", b"")

                    task = await UITask.create_task(
                        task_id=task_id,
                        conversation_id=conversation_id,
                        project_name=project,
                        task_type=TaskType.IMAGE_UPLOAD,
                        filename=filename,
                        file_size=len(file_content),
                        user_requirement=user_requirement,
                        collection_name=collection_info["ui_element_collection"],
                    )

                    # 验证图片格式
                    if not self._validate_image_format(filename):
                        await task.update_status(
                            TaskStatus.FAILED,
                            error_message=f"不支持的图片格式: {Path(filename).suffix}",
                        )
                        result["failed_count"] += 1
                        result["tasks"].append(
                            {
                                "task_id": task_id,
                                "filename": filename,
                                "status": "failed",
                                "error": "不支持的图片格式",
                            }
                        )
                        continue

                    # 计算MD5并检查重复
                    file_md5 = hashlib.md5(file_content).hexdigest()
                    task.file_md5 = file_md5
                    await task.save()

                    is_duplicate = await RAGFileRecord.is_file_exists_in_collection(
                        file_md5, collection_info["ui_element_collection"]
                    )

                    if is_duplicate:
                        await task.update_status(
                            TaskStatus.DUPLICATE,
                            progress=100,
                            current_step="文件已存在，跳过处理",
                        )
                        result["duplicate_count"] += 1
                        result["tasks"].append(
                            {
                                "task_id": task_id,
                                "filename": filename,
                                "status": "duplicate",
                                "message": "文件已存在",
                            }
                        )
                        continue

                    # 保存图片文件
                    image_path = await self._save_image_file(
                        filename, file_content, conversation_id
                    )
                    task.file_path = image_path
                    await task.update_status(
                        TaskStatus.PROCESSING,
                        progress=50,
                        current_step="文件保存完成，准备分析",
                    )

                    # 记录文件到数据库
                    await RAGFileRecord.create_record(
                        filename=filename,
                        file_md5=file_md5,
                        file_size=len(file_content),
                        collection_name=collection_info["ui_element_collection"],
                        user_id=conversation_id,
                    )

                    # 启动UI分析智能体
                    await self._start_ui_analysis(
                        task_id=task_id,
                        conversation_id=conversation_id,
                        image_path=image_path,
                        user_requirement=user_requirement,
                        filename=filename,
                    )

                    result["processed_count"] += 1
                    result["tasks"].append(
                        {
                            "task_id": task_id,
                            "filename": filename,
                            "status": "analyzing",  # 状态改为analyzing
                            "image_path": image_path,
                            "file_md5": file_md5,
                        }
                    )

                    logger.info(f"✅ 图片处理成功，已启动UI分析: {filename}")

                except Exception as e:
                    logger.error(f"❌ 处理图片失败: {filename} | 错误: {e}")
                    result["failed_count"] += 1
                    if "task" in locals():
                        await task.update_status(
                            TaskStatus.FAILED, error_message=str(e)
                        )
                        result["tasks"].append(
                            {
                                "task_id": task.task_id,
                                "filename": filename,
                                "status": "failed",
                                "error": str(e),
                            }
                        )

            logger.success(
                f"✅ 图片上传处理完成 | 对话ID: {conversation_id} | "
                f"成功: {result['processed_count']} | "
                f"失败: {result['failed_count']} | "
                f"重复: {result['duplicate_count']}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ 图片上传处理失败 | 对话ID: {conversation_id} | 错误: {e}")
            raise

    async def _start_ui_analysis(
        self,
        task_id: str,
        conversation_id: str,
        image_path: str,
        user_requirement: str,
        filename: str,
    ):
        """启动UI分析智能体"""
        try:
            logger.info(f"🚀 [UI分析启动] 任务ID: {task_id} | 图片: {filename}")

            # 确保运行时已初始化
            logger.debug(f"🔧 [UI分析启动] 初始化运行时 | 对话ID: {conversation_id}")
            await self.runtime.initialize_runtime(conversation_id)

            # 使用runtime启动UI分析
            await self.runtime.start_ui_analysis(
                conversation_id=conversation_id,
                image_paths=[image_path],  # runtime期望的是列表
                user_requirement=user_requirement,
                task_ids=[task_id],  # 传递task_id列表
            )

            logger.success(
                f"✅ [UI分析启动] UI分析已通过runtime启动 | 任务ID: {task_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI分析启动] 启动UI分析失败 | 任务ID: {task_id} | 错误: {e}"
            )

            # 更新任务状态为失败
            task = await UITask.get_by_task_id(task_id)
            if task:
                await task.update_status(
                    TaskStatus.FAILED, error_message=f"启动UI分析失败: {str(e)}"
                )

    async def _ensure_project_exists(self, project_name: str, conversation_id: str):
        """确保项目存在，不存在则创建"""
        logger.info(f"🔍 [项目检查] 检查项目是否存在: {project_name}")
        from backend.schemas.project import ProjectCreate

        project = await project_controller.get_by_name(project_name)
        if not project:
            logger.info(f"📝 [项目创建] 项目不存在，创建新项目: {project_name}")

            project_data = ProjectCreate(
                name=project_name,
                display_name=project_name,
                description=f"UI测试项目 - {project_name}",
                is_active=True,
            )
            project = await project_controller.create_project(project_data)

            logger.success(f"✅ [项目创建] 项目创建成功: {project_name}")
        else:
            logger.info(f"✅ [项目检查] 项目已存在: {project_name}")

        return project

    async def _ensure_collections_exist(
        self, project_name: str, conversation_id: str
    ) -> dict:
        """确保项目的Collection存在，不存在则创建"""
        from backend.conf.rag_config import get_rag_config
        from backend.models.rag import RAGCollection
        from backend.services.rag.collection_service import collection_service

        # 清理项目名称，确保符合Milvus命名规则
        sanitized_project_name = self._sanitize_collection_name(project_name)
        ui_element_collection = f"{sanitized_project_name}_ui_element"
        document_collection = f"{sanitized_project_name}_document"

        logger.info(
            f"🔧 [Collection命名] 原项目名: {project_name} → 清理后: {sanitized_project_name}"
        )
        logger.info(f"📝 [Collection命名] UI元素Collection: {ui_element_collection}")
        logger.info(f"📝 [Collection命名] 文档Collection: {document_collection}")

        logger.info(f"🔍 [Collection检查] 检查Collection是否存在")

        collections_created = []

        # 获取RAG配置以获取默认参数
        rag_config = get_rag_config()
        default_dimension = rag_config.milvus.dimension

        # 检查UI元素Collection
        ui_collection = await RAGCollection.filter(name=ui_element_collection).first()
        if not ui_collection:
            logger.info(
                f"📝 [Collection创建] 创建UI元素Collection: {ui_element_collection}"
            )

            collection_data = {
                "name": ui_element_collection,
                "display_name": f"{project_name} UI元素知识库",
                "description": f"存储 {project_name} 项目的UI元素分析结果",
                "business_type": "ui_testing",
                "dimension": default_dimension,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 5,
                "similarity_threshold": 0.7,
            }

            result = await collection_service.create_collection(collection_data)

            if result.get("success", False):
                collections_created.append(ui_element_collection)
        else:
            # Collection存在，确保向量数据库连接
            logger.info(
                f"🔍 [Collection检查] 确保UI元素Collection向量数据库连接: {ui_element_collection}"
            )
            await collection_service.ensure_collection_connected(ui_element_collection)

        # 检查文档Collection
        doc_collection = await RAGCollection.filter(name=document_collection).first()
        if not doc_collection:
            logger.info(
                f"📝 [Collection创建] 创建文档Collection: {document_collection}"
            )

            collection_data = {
                "name": document_collection,
                "display_name": f"{project_name} 文档知识库",
                "description": f"存储 {project_name} 项目的相关文档",
                "business_type": "general",
                "dimension": default_dimension,
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "top_k": 5,
                "similarity_threshold": 0.7,
            }

            result = await collection_service.create_collection(collection_data)

            if result.get("success", False):
                collections_created.append(document_collection)
        else:
            # Collection存在，确保向量数据库连接
            logger.info(
                f"🔍 [Collection检查] 确保文档Collection向量数据库连接: {document_collection}"
            )
            await collection_service.ensure_collection_connected(document_collection)

        return {
            "ui_element_collection": ui_element_collection,
            "document_collection": document_collection,
            "collections_created": collections_created,
        }

    def _validate_image_format(self, filename: str) -> bool:
        """验证图片格式"""
        if not filename:
            return False

        file_extension = Path(filename).suffix.lower()
        return file_extension in self.supported_image_formats

    async def _save_image_file(
        self, filename: str, file_content: bytes, conversation_id: str
    ) -> str:
        """保存图片文件到本地"""
        # 创建上传目录
        upload_dir = Path("uploads/ui_testing/images")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名（时间戳 + 原文件名）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(filename).suffix
        unique_filename = f"{timestamp}_{filename}"
        image_path = upload_dir / unique_filename

        logger.info(f"💾 [文件保存] 保存图片到: {image_path}")

        # 保存文件
        with open(image_path, "wb") as f:
            f.write(file_content)

        logger.success(f"✅ [文件保存] 图片保存成功: {image_path}")
        return str(image_path)

    async def start_streaming_image_upload(
        self,
        project: str,
        image_files: List[dict],
        conversation_id: str,
        user_requirement: str = "",
    ) -> None:
        """
        启动流式图片上传和分析

        Args:
            project: 项目名称
            image_files: 图片文件数据列表
            conversation_id: 对话ID
            user_requirement: 用户需求
        """
        logger.info(f"📷 [UI测试服务] 启动流式图片上传 | 对话ID: {conversation_id}")
        logger.info(f"🏗️ 项目: {project}")
        logger.info(f"📷 图片数量: {len(image_files)}")
        logger.info(f"📝 用户需求: {user_requirement[:100]}...")

        try:
            # 验证模型配置
            if not validate_model_configs():
                error_msg = "模型配置验证失败，请检查配置"
                logger.error(f"❌ [UI测试服务] {error_msg}")
                await put_message_to_queue(
                    conversation_id,
                    json.dumps(
                        {
                            "type": "error",
                            "source": "system",
                            "content": error_msg,
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat(),
                        },
                        ensure_ascii=False,
                    ),
                )
                return

            # 初始化运行时
            await self.runtime.initialize_runtime(conversation_id)

            # 发送系统开始消息
            await put_message_to_queue(
                conversation_id,
                json.dumps(
                    {
                        "type": "system_start",
                        "message": "图片上传和分析开始",
                        "content": f"正在处理 {len(image_files)} 张图片的上传和分析...",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                ),
            )

            # 启动图片上传处理
            await self.runtime.start_image_upload(
                conversation_id, project, image_files, user_requirement
            )

            logger.success(
                f"✅ [UI测试服务] 流式图片上传启动成功 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(f"❌ [UI测试服务] 流式图片上传启动失败: {e}")

            # 发送错误消息
            await put_message_to_queue(
                conversation_id,
                json.dumps(
                    {
                        "type": "error",
                        "source": "system",
                        "content": f"图片上传启动失败: {str(e)}",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                ),
            )
            raise

    async def start_streaming_analysis(
        self, conversation_id: str, image_paths: List[str], user_requirement: str
    ) -> None:
        """
        启动流式UI测试分析

        Args:
            conversation_id: 对话ID
            image_paths: 图片路径列表
            user_requirement: 用户需求
        """
        logger.info(f"🌊 [UI测试服务] 启动流式分析 | 对话ID: {conversation_id}")
        logger.info(f"📷 图片数量: {len(image_paths)}")
        logger.info(f"📝 用户需求: {user_requirement[:100]}...")

        try:
            # 验证模型配置
            configs = validate_model_configs()
            if not any(configs.values()):
                error_msg = "没有可用的模型配置"
                logger.error(f"❌ [UI测试服务] {error_msg}")
                await put_message_to_queue(
                    conversation_id,
                    json.dumps(
                        {
                            "type": "error",
                            "source": "system",
                            "content": error_msg,
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat(),
                        },
                        ensure_ascii=False,
                    ),
                )
                return

            # 验证图片文件
            valid_image_paths = []
            for image_path in image_paths:
                if Path(image_path).exists():
                    valid_image_paths.append(image_path)
                    logger.debug(f"✅ 图片文件验证通过: {image_path}")
                else:
                    logger.warning(f"⚠️ 图片文件不存在: {image_path}")

            if not valid_image_paths:
                error_msg = "没有有效的图片文件"
                logger.error(f"❌ [UI测试服务] {error_msg}")
                await put_message_to_queue(
                    conversation_id,
                    json.dumps(
                        {
                            "type": "error",
                            "source": "system",
                            "content": error_msg,
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat(),
                        },
                        ensure_ascii=False,
                    ),
                )
                return

            logger.info(f"✅ 验证通过，有效图片数量: {len(valid_image_paths)}")

            # 初始化运行时
            await self.runtime.initialize_runtime(conversation_id)

            # 发送系统开始消息
            await put_message_to_queue(
                conversation_id,
                json.dumps(
                    {
                        "type": "system_start",
                        "message": "四智能体协作分析开始",
                        "content": "正在启动UI分析、交互分析、Midscene生成和脚本生成智能体...",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                ),
            )

            # 启动UI分析
            await self.runtime.start_ui_analysis(
                conversation_id, valid_image_paths, user_requirement
            )

            # 保存分析请求到内存
            await self.memory_manager.save_to_memory(
                conversation_id,
                {
                    "type": "ui_analysis_request",
                    "image_paths": valid_image_paths,
                    "user_requirement": user_requirement,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.success(
                f"✅ [UI测试服务] 流式分析启动成功 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 流式分析启动失败 | 对话ID: {conversation_id} | 错误: {e}"
            )

            # 发送错误消息
            await put_message_to_queue(
                conversation_id,
                json.dumps(
                    {
                        "type": "system_error",
                        "message": "系统启动失败",
                        "content": f"UI测试分析启动失败: {str(e)}",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                ),
            )
            raise

    async def get_streaming_response(self, conversation_id: str):
        """
        获取流式响应

        Args:
            conversation_id: 对话ID

        Returns:
            异步生成器，产生SSE格式的消息
        """
        logger.info(f"📡 [UI测试服务] 获取流式响应 | 对话ID: {conversation_id}")

        try:
            # 使用AI核心框架的流式SSE消息获取函数（内部已有300秒超时）
            async for message in get_streaming_sse_messages_from_queue(conversation_id):
                yield message

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 流式响应获取失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            # 发送错误消息
            error_message = f"data: {json.dumps({'type': 'error', 'content': f'流式响应获取失败: {str(e)}'}, ensure_ascii=False)}\n\n"
            yield error_message

    async def cleanup_conversation(self, conversation_id: str) -> None:
        """
        清理对话资源

        Args:
            conversation_id: 对话ID
        """
        logger.info(f"🗑️ [UI测试服务] 清理对话资源 | 对话ID: {conversation_id}")

        try:
            # 清理运行时（包括队列）
            await self.runtime.cleanup_runtime(conversation_id)

            logger.success(
                f"✅ [UI测试服务] 对话资源清理完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 对话资源清理失败 | 对话ID: {conversation_id} | 错误: {e}"
            )

    async def get_conversation_history(self, conversation_id: str) -> List[dict]:
        """
        获取对话历史

        Args:
            conversation_id: 对话ID

        Returns:
            对话历史列表
        """
        logger.info(f"📚 [UI测试服务] 获取对话历史 | 对话ID: {conversation_id}")

        try:
            # 使用内存管理器获取对话历史
            memory = await self.memory_manager.get_memory(conversation_id)
            if memory:
                history = await memory.get_messages()
                logger.info(f"📖 获取到 {len(history)} 条历史记录")
                return history
            else:
                logger.info("📭 没有找到对话历史")
                return []

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 获取对话历史失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            return []

    async def save_analysis_result(
        self, conversation_id: str, result_type: str, content: str
    ) -> None:
        """
        保存分析结果

        Args:
            conversation_id: 对话ID
            result_type: 结果类型
            content: 结果内容
        """
        logger.info(
            f"💾 [UI测试服务] 保存分析结果 | 对话ID: {conversation_id} | 类型: {result_type}"
        )

        try:
            await self.memory_manager.save_to_memory(
                conversation_id,
                {
                    "type": result_type,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.success(f"✅ 分析结果已保存 | 类型: {result_type}")

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 保存分析结果失败 | 对话ID: {conversation_id} | 错误: {e}"
            )

    def get_service_status(self) -> dict:
        """
        获取服务状态

        Returns:
            服务状态信息
        """
        try:
            configs = validate_model_configs()
            return {
                "service_name": "UI测试服务",
                "status": "running",
                "framework": "AI核心框架",
                "model_configs": configs,
                "runtime_status": "initialized",
                "memory_manager": "available",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"❌ [UI测试服务] 获取服务状态失败: {e}")
            return {
                "service_name": "UI测试服务",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# 创建全局服务实例
ui_testing_service = UITestingService()

# 导出接口
__all__ = [
    "UITestingService",
    "ui_testing_service",
]
