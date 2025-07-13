"""
UI测试任务管理模型
用于跟踪图片上传和分析任务的状态
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from tortoise import fields
from tortoise.models import Model


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待处理
    UPLOADING = "uploading"  # 上传中
    VALIDATING = "validating"  # 验证中
    DUPLICATE = "duplicate"  # 重复文件
    PROCESSING = "processing"  # 处理中
    ANALYZING = "analyzing"  # 分析中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class TaskType(str, Enum):
    """任务类型枚举"""

    IMAGE_UPLOAD = "image_upload"  # 图片上传
    IMAGE_ANALYSIS = "image_analysis"  # 图片分析
    UI_ELEMENT_ANALYSIS = "ui_element"  # UI元素分析
    INTERACTION_ANALYSIS = "interaction"  # 交互分析
    MIDSCENE_GENERATION = "midscene"  # Midscene生成
    SCRIPT_GENERATION = "script"  # 脚本生成


class UITask(Model):
    """UI测试任务模型"""

    id = fields.IntField(pk=True)

    # 基本信息
    task_id = fields.CharField(max_length=100, unique=True, description="任务唯一ID")
    conversation_id = fields.CharField(max_length=100, description="对话ID")
    project_name = fields.CharField(max_length=100, description="项目名称")

    # 任务信息
    task_type = fields.CharEnumField(TaskType, description="任务类型")
    status = fields.CharEnumField(
        TaskStatus, default=TaskStatus.PENDING, description="任务状态"
    )

    # 文件信息
    filename = fields.CharField(max_length=255, null=True, description="文件名")
    file_path = fields.CharField(max_length=500, null=True, description="文件路径")
    file_size = fields.BigIntField(null=True, description="文件大小(字节)")
    file_md5 = fields.CharField(max_length=32, null=True, description="文件MD5")

    # 处理信息
    user_requirement = fields.TextField(null=True, description="用户需求")
    progress = fields.IntField(default=0, description="进度百分比(0-100)")
    current_step = fields.CharField(max_length=200, null=True, description="当前步骤")

    # 结果信息
    result_data = fields.JSONField(default=dict, description="结果数据")
    error_message = fields.TextField(null=True, description="错误信息")

    # 关联信息
    parent_task_id = fields.CharField(max_length=100, null=True, description="父任务ID")
    collection_name = fields.CharField(
        max_length=100, null=True, description="RAG Collection名称"
    )

    # 时间信息
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    started_at = fields.DatetimeField(null=True, description="开始时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")

    # 元数据
    metadata = fields.JSONField(default=dict, description="元数据")

    class Meta:
        table = "ui_tasks"
        table_description = "UI测试任务表"
        indexes = [
            ("task_id",),
            ("conversation_id",),
            ("project_name",),
            ("status",),
            ("task_type",),
            ("created_at",),
        ]

    def __str__(self):
        return f"UITask({self.task_id}, {self.task_type}, {self.status})"

    @property
    def duration(self) -> Optional[float]:
        """计算任务持续时间(秒)"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]

    @property
    def is_processing(self) -> bool:
        """是否正在处理"""
        return self.status in [
            TaskStatus.UPLOADING,
            TaskStatus.VALIDATING,
            TaskStatus.PROCESSING,
            TaskStatus.ANALYZING,
        ]

    async def update_status(
        self,
        status: TaskStatus,
        progress: Optional[int] = None,
        current_step: Optional[str] = None,
        error_message: Optional[str] = None,
        result_data: Optional[dict] = None,
    ) -> None:
        """更新任务状态"""
        self.status = status

        if progress is not None:
            self.progress = max(0, min(100, progress))

        if current_step is not None:
            self.current_step = current_step

        if error_message is not None:
            self.error_message = error_message

        if result_data is not None:
            if self.result_data:
                self.result_data.update(result_data)
            else:
                self.result_data = result_data

        # 设置时间戳
        if status == TaskStatus.PROCESSING and not self.started_at:
            self.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            if not self.completed_at:
                self.completed_at = datetime.now()

        await self.save()

    async def add_metadata(self, key: str, value: any) -> None:
        """添加元数据"""
        if not self.metadata:
            self.metadata = {}
        self.metadata[key] = value
        await self.save()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "conversation_id": self.conversation_id,
            "project_name": self.project_name,
            "task_type": self.task_type,
            "status": self.status,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_md5": self.file_md5,
            "user_requirement": self.user_requirement,
            "progress": self.progress,
            "current_step": self.current_step,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "parent_task_id": self.parent_task_id,
            "collection_name": self.collection_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration": self.duration,
            "metadata": self.metadata,
        }

    @classmethod
    async def create_task(
        cls,
        task_id: str,
        conversation_id: str,
        project_name: str,
        task_type: TaskType,
        filename: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        file_md5: Optional[str] = None,
        user_requirement: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        collection_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "UITask":
        """创建新任务"""
        return await cls.create(
            task_id=task_id,
            conversation_id=conversation_id,
            project_name=project_name,
            task_type=task_type,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_md5=file_md5,
            user_requirement=user_requirement,
            parent_task_id=parent_task_id,
            collection_name=collection_name,
            metadata=metadata or {},
        )

    @classmethod
    async def get_by_task_id(cls, task_id: str) -> Optional["UITask"]:
        """根据任务ID获取任务"""
        return await cls.filter(task_id=task_id).first()

    @classmethod
    async def get_tasks_by_conversation(cls, conversation_id: str) -> list["UITask"]:
        """获取对话的所有任务"""
        return await cls.filter(conversation_id=conversation_id).order_by("-created_at")

    @classmethod
    async def get_tasks_by_project(cls, project_name: str) -> list["UITask"]:
        """获取项目的所有任务"""
        return await cls.filter(project_name=project_name).order_by("-created_at")

    @classmethod
    async def get_processing_tasks(cls) -> list["UITask"]:
        """获取所有正在处理的任务"""
        return await cls.filter(
            status__in=[
                TaskStatus.UPLOADING,
                TaskStatus.VALIDATING,
                TaskStatus.PROCESSING,
                TaskStatus.ANALYZING,
            ]
        ).order_by("-created_at")
