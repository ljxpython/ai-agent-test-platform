"""
UI测试相关的Schema定义
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UITestRequest(BaseModel):
    """UI测试请求Schema"""

    conversation_id: str = Field(..., description="对话ID")
    user_requirement: str = Field(..., description="用户需求描述")
    image_path: Optional[str] = Field(None, description="图片路径")


class UITestResponse(BaseModel):
    """UI测试响应Schema"""

    conversation_id: str = Field(..., description="对话ID")
    status: str = Field(..., description="处理状态")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")


class MidsceneScriptRequest(BaseModel):
    """Midscene脚本生成请求Schema"""

    conversation_id: str = Field(..., description="对话ID")
    ui_analysis: str = Field(..., description="UI分析结果")
    user_requirement: str = Field(..., description="用户需求")


class MidsceneScriptResponse(BaseModel):
    """Midscene脚本生成响应Schema"""

    conversation_id: str = Field(..., description="对话ID")
    yaml_script: str = Field(..., description="YAML格式脚本")
    playwright_script: str = Field(..., description="Playwright格式脚本")
    script_info: Dict[str, Any] = Field(..., description="脚本信息")


class UIImageUploadRequest(BaseModel):
    """UI图片上传请求Schema"""

    project: str = Field(..., description="项目名称")
    conversation_id: str = Field(..., description="对话ID")
    user_requirement: Optional[str] = Field("", description="用户需求描述")


class UIImageUploadResponse(BaseModel):
    """UI图片上传响应Schema"""

    conversation_id: str = Field(..., description="对话ID")
    project: str = Field(..., description="项目名称")
    status: str = Field(..., description="处理状态")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")


class ImageUploadResult(BaseModel):
    """图片上传结果Schema"""

    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小(字节)")
    file_md5: str = Field(..., description="文件MD5")
    collection_name: str = Field(..., description="存储的Collection名称")
    is_duplicate: bool = Field(..., description="是否为重复文件")
    analysis_result: Optional[str] = Field(None, description="AI分析结果")
    rag_saved: bool = Field(False, description="是否已保存到RAG知识库")
    processing_time: float = Field(..., description="处理耗时(秒)")


class ProjectCollectionInfo(BaseModel):
    """项目Collection信息Schema"""

    project_name: str = Field(..., description="项目名称")
    ui_element_collection: str = Field(..., description="UI元素Collection名称")
    document_collection: str = Field(..., description="文档Collection名称")
    collections_created: List[str] = Field(
        default_factory=list, description="新创建的Collection列表"
    )
