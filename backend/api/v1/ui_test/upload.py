"""
UI测试图片上传API接口
支持图片上传、实时状态更新、MD5重复检测和智能体分析
"""

import asyncio
import uuid
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger

# 响应处理
from backend.api_core.response import Success

# 数据库模型
from backend.models.ui_task import UITask

# Schema
from backend.schemas.ui_test import UIImageUploadRequest, UIImageUploadResponse

# 核心服务
from backend.services.ui_testing.ui_service import ui_testing_service

# 创建路由器
ui_upload_router = APIRouter()


@ui_upload_router.post("/upload/images/batch")
async def upload_images_batch(
    project: str = Form(..., description="项目名称"),
    conversation_id: Optional[str] = Form(None, description="对话ID"),
    user_requirement: str = Form("", description="用户需求描述"),
    images: List[UploadFile] = File(..., description="图片文件列表"),
):
    """
    UI测试图片批量上传接口

    功能：
    1. 检查项目是否存在，不存在则创建
    2. 检查Collection是否存在，不存在则创建 ({project}_ui_element, {project}_document)
    3. 批量验证图片格式，过滤不支持的格式
    4. MD5重复检测，跳过已上传的图片
    5. 启动智能体分析
    6. 直接返回处理结果

    Args:
        project: 项目名称
        conversation_id: 对话ID（可选，不提供则自动生成）
        user_requirement: 用户需求描述
        images: 上传的图片文件列表

    Returns:
        dict: 上传处理结果
    """
    # 生成或使用提供的对话ID
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    logger.info(f"📷 [API-图片批量上传-流式] 收到图片上传请求")
    logger.info(f"   📋 对话ID: {conversation_id}")
    logger.info(f"   🏗️ 项目: {project}")
    logger.info(f"   📄 文件数量: {len(images)}")
    logger.info(f"   📄 文件列表: {[img.filename for img in images]}")
    logger.info(
        f"   📝 用户需求: {user_requirement[:100]}..."
        if len(user_requirement) > 100
        else f"   📝 用户需求: {user_requirement}"
    )
    logger.info(f"   🌐 请求方法: POST /api/ui_test/upload/images/streaming")

    try:
        # 验证基本参数
        if not project or not project.strip():
            raise HTTPException(status_code=400, detail="项目名称不能为空")

        if not images or len(images) == 0:
            raise HTTPException(status_code=400, detail="至少需要上传一个图片文件")

        # 验证文件名
        for img in images:
            if not img.filename:
                raise HTTPException(status_code=400, detail="所有文件都必须有文件名")

        # 处理图片上传和分析
        logger.info(f"🚀 [API-图片批量上传] 开始处理 | 对话ID: {conversation_id}")

        # 准备图片文件数据
        image_files_data = []
        for img in images:
            content = await img.read()
            image_files_data.append(
                {
                    "filename": img.filename,
                    "content": content,
                    "size": len(content),
                }
            )

        # 直接处理图片上传（不使用流式输出）
        result = await ui_testing_service.process_image_upload(
            project=project.strip(),
            image_files=image_files_data,
            conversation_id=conversation_id,
            user_requirement=user_requirement.strip(),
        )

        logger.info(f"✅ [API-图片批量上传] 处理完成 | 对话ID: {conversation_id}")

        return {
            "code": 200,
            "msg": "图片上传处理成功",
            "data": {
                "conversation_id": conversation_id,
                "project": project,
                "image_count": len(image_files_data),
                "processed_count": result.get("processed_count", 0),
                "failed_count": result.get("failed_count", 0),
                "duplicate_count": result.get("duplicate_count", 0),
                "tasks": result.get("tasks", []),
                "message": "图片上传处理ing...",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API-图片批量上传] 请求处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")


@ui_upload_router.post("/upload/images")
async def upload_images_sync(
    project: str = Form(..., description="项目名称"),
    conversation_id: Optional[str] = Form(None, description="对话ID"),
    user_requirement: str = Form("", description="用户需求描述"),
    images: List[UploadFile] = File(..., description="图片文件列表"),
):
    """
    UI测试图片批量上传接口 - 同步模式（用于测试）

    Args:
        project: 项目名称
        conversation_id: 对话ID（可选，不提供则自动生成）
        user_requirement: 用户需求描述
        images: 上传的图片文件列表

    Returns:
        上传结果
    """
    # 生成或使用提供的对话ID
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    logger.info(f"📷 [API-图片批量上传-同步] 收到图片上传请求")
    logger.info(f"   📋 对话ID: {conversation_id}")
    logger.info(f"   🏗️ 项目: {project}")
    logger.info(f"   📄 文件数量: {len(images)}")

    try:
        # 验证基本参数
        if not project or not project.strip():
            raise HTTPException(status_code=400, detail="项目名称不能为空")

        if not images or len(images) == 0:
            raise HTTPException(status_code=400, detail="至少需要上传一个图片文件")

        # 验证文件名
        for img in images:
            if not img.filename:
                raise HTTPException(status_code=400, detail="所有文件都必须有文件名")

        # 准备图片文件数据
        image_files_data = []
        for img in images:
            content = await img.read()
            image_files_data.append(
                {
                    "filename": img.filename,
                    "content": content,
                    "size": len(content),
                }
            )

        # 启动上传和分析（同步等待）
        await ui_testing_service.start_streaming_image_upload(
            project=project.strip(),
            image_files=image_files_data,
            conversation_id=conversation_id,
            user_requirement=user_requirement.strip(),
        )

        logger.success(
            f"✅ [API-图片批量上传-同步] 上传启动完成 | 对话ID: {conversation_id}"
        )

        return Success(
            data={
                "conversation_id": conversation_id,
                "project": project,
                "image_count": len(images),
                "message": "图片上传和分析已启动，请通过任务状态接口查询进度",
            },
            msg="图片上传启动成功",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API-图片上传-同步] 上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")


@ui_upload_router.get("/tasks/status/{conversation_id}")
async def get_tasks_status(conversation_id: str):
    """
    获取对话的所有任务状态

    Args:
        conversation_id: 对话ID

    Returns:
        任务状态列表
    """
    logger.info(f"📊 [API-任务状态] 查询任务状态 | 对话ID: {conversation_id}")

    try:
        # 查询对话的所有任务
        tasks = await UITask.get_tasks_by_conversation(conversation_id)

        # 转换为字典格式
        tasks_data = [task.to_dict() for task in tasks]

        # 统计信息
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.is_completed])
        processing_tasks = len([t for t in tasks if t.is_processing])
        failed_tasks = len([t for t in tasks if t.status.value == "failed"])

        return Success(
            data={
                "conversation_id": conversation_id,
                "summary": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "processing_tasks": processing_tasks,
                    "failed_tasks": failed_tasks,
                },
                "tasks": tasks_data,
            },
            msg="任务状态查询成功",
        )

    except Exception as e:
        logger.error(f"❌ [API-任务状态] 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"任务状态查询失败: {str(e)}")


@ui_upload_router.get("/task/status/{task_id}")
async def get_task_status(task_id: str):
    """
    获取单个任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务详细状态
    """
    logger.info(f"📊 [API-单任务状态] 查询任务状态 | 任务ID: {task_id}")

    try:
        # 查询任务
        task = await UITask.get_by_task_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")

        return Success(data=task.to_dict(), msg="任务状态查询成功")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API-单任务状态] 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"任务状态查询失败: {str(e)}")


@ui_upload_router.get("/tasks/project/{project_name}")
async def get_project_tasks(project_name: str):
    """
    获取项目的所有任务

    Args:
        project_name: 项目名称

    Returns:
        项目任务列表
    """
    logger.info(f"📊 [API-项目任务] 查询项目任务 | 项目: {project_name}")

    try:
        # 查询项目的所有任务
        tasks = await UITask.get_tasks_by_project(project_name)

        # 转换为字典格式
        tasks_data = [task.to_dict() for task in tasks]

        # 统计信息
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.is_completed])
        processing_tasks = len([t for t in tasks if t.is_processing])

        return Success(
            data={
                "project_name": project_name,
                "summary": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "processing_tasks": processing_tasks,
                },
                "tasks": tasks_data,
            },
            msg="项目任务查询成功",
        )

    except Exception as e:
        logger.error(f"❌ [API-项目任务] 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"项目任务查询失败: {str(e)}")


@ui_upload_router.get("/tasks/search")
async def search_tasks(
    project: Optional[str] = Query(None, description="项目名称"),
    filename: Optional[str] = Query(None, description="图片文件名"),
    task_id: Optional[str] = Query(None, description="任务ID"),
    status: Optional[str] = Query(None, description="任务状态"),
    limit: int = Query(50, description="返回数量限制"),
    offset: int = Query(0, description="偏移量"),
):
    """
    搜索图片处理任务

    支持根据项目、图片文件名、任务ID、状态等条件查询

    Args:
        project: 项目名称
        filename: 图片文件名（支持模糊匹配）
        task_id: 任务ID
        status: 任务状态 (pending/processing/analyzing/completed/failed)
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        匹配的任务列表
    """
    logger.info(
        f"🔍 [API-任务搜索] 搜索任务 | 项目: {project} | 文件名: {filename} | 任务ID: {task_id} | 状态: {status}"
    )

    try:
        # 构建查询条件
        query = UITask.all()

        if project:
            query = query.filter(project_name=project)

        if filename:
            query = query.filter(filename__icontains=filename)

        if task_id:
            query = query.filter(task_id=task_id)

        if status:
            query = query.filter(status=status)

        # 分页查询
        total_count = await query.count()
        tasks = await query.offset(offset).limit(limit).order_by("-created_at").all()

        # 转换为字典格式
        tasks_data = [task.to_dict() for task in tasks]

        # 统计信息
        status_counts = {}
        for task in tasks:
            status_key = task.status.value
            status_counts[status_key] = status_counts.get(status_key, 0) + 1

        return Success(
            data={
                "total_count": total_count,
                "returned_count": len(tasks),
                "offset": offset,
                "limit": limit,
                "status_counts": status_counts,
                "tasks": tasks_data,
                "filters": {
                    "project": project,
                    "filename": filename,
                    "task_id": task_id,
                    "status": status,
                },
            },
            msg="任务搜索成功",
        )

    except Exception as e:
        logger.error(f"❌ [API-任务搜索] 搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"任务搜索失败: {str(e)}")


@ui_upload_router.get("/tasks/stats")
async def get_tasks_statistics(
    project: Optional[str] = Query(None, description="项目名称"),
    days: int = Query(7, description="统计天数"),
):
    """
    获取任务统计信息

    Args:
        project: 项目名称（可选，不提供则统计所有项目）
        days: 统计天数（默认7天）

    Returns:
        任务统计数据
    """
    logger.info(f"📊 [API-任务统计] 获取统计信息 | 项目: {project} | 天数: {days}")

    try:
        from datetime import datetime, timedelta

        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 构建查询
        query = UITask.filter(created_at__gte=start_date)
        if project:
            query = query.filter(project_name=project)

        # 获取所有任务
        tasks = await query.all()

        # 统计数据
        total_tasks = len(tasks)
        status_stats = {}
        project_stats = {}
        daily_stats = {}

        for task in tasks:
            # 状态统计
            status_key = task.status.value
            status_stats[status_key] = status_stats.get(status_key, 0) + 1

            # 项目统计
            project_key = task.project_name
            if project_key not in project_stats:
                project_stats[project_key] = {"total": 0, "completed": 0, "failed": 0}
            project_stats[project_key]["total"] += 1
            if task.status.value == "completed":
                project_stats[project_key]["completed"] += 1
            elif task.status.value == "failed":
                project_stats[project_key]["failed"] += 1

            # 每日统计
            date_key = task.created_at.strftime("%Y-%m-%d")
            if date_key not in daily_stats:
                daily_stats[date_key] = {"total": 0, "completed": 0, "failed": 0}
            daily_stats[date_key]["total"] += 1
            if task.status.value == "completed":
                daily_stats[date_key]["completed"] += 1
            elif task.status.value == "failed":
                daily_stats[date_key]["failed"] += 1

        # 计算成功率
        completed_count = status_stats.get("completed", 0)
        success_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0

        return Success(
            data={
                "time_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days,
                },
                "summary": {
                    "total_tasks": total_tasks,
                    "success_rate": round(success_rate, 2),
                    "completed_tasks": completed_count,
                    "failed_tasks": status_stats.get("failed", 0),
                    "processing_tasks": status_stats.get("processing", 0)
                    + status_stats.get("analyzing", 0),
                },
                "status_stats": status_stats,
                "project_stats": project_stats,
                "daily_stats": daily_stats,
                "filter": {"project": project},
            },
            msg="统计信息获取成功",
        )

    except Exception as e:
        logger.error(f"❌ [API-任务统计] 获取失败: {e}")
        raise HTTPException(status_code=500, detail=f"统计信息获取失败: {str(e)}")


@ui_upload_router.get("/supported-formats")
async def get_supported_formats():
    """
    获取支持的图片格式

    Returns:
        支持的图片格式列表
    """
    logger.info(f"📋 [API-支持格式] 查询支持的图片格式")

    supported_formats = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

    return Success(
        data={
            "supported_formats": supported_formats,
            "description": "支持的图片格式",
        },
        msg="查询成功",
    )
