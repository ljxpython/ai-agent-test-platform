"""
FastAPI主服务
知识库管理系统后端API
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    # 尝试相对导入 (作为包使用时)
    from .config import ALLOWED_EXTENSIONS, CORS_ORIGINS, MAX_FILE_SIZE, UPLOAD_DIR
    from .database import DocumentDB, init_database
    from .document_processor import DocumentProcessor
    from .rag_service import RAGService
except ImportError:
    # 绝对导入 (直接运行时)
    from config import ALLOWED_EXTENSIONS, CORS_ORIGINS, MAX_FILE_SIZE, UPLOAD_DIR
    from database import DocumentDB, init_database
    from document_processor import DocumentProcessor
    from rag_service import RAGService


# 初始化FastAPI应用
app = FastAPI(
    title="知识库管理系统API",
    description="基于RAG的知识库管理和检索系统",
    version="1.0.0",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_database()

# 初始化服务
document_processor = DocumentProcessor()
rag_service = RAGService()


# Pydantic模型
class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    upload_time: str
    status: str
    chunk_count: int
    description: Optional[str] = None
    tags: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    k: int = 4
    search_type: str = "similarity"


class QuestionRequest(BaseModel):
    question: str


# API路由
@app.get("/")
async def root():
    """根路径"""
    return {"message": "知识库管理系统API", "version": "1.0.0", "docs": "/docs"}


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
):
    """
    上传文档
    """
    try:
        # 验证文件大小
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制({MAX_FILE_SIZE / 1024 / 1024}MB)",
            )

        # 验证文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")

        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 创建数据库记录
        doc_id = DocumentDB.create_document(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_ext,
            description=description,
            tags=tags,
        )

        return JSONResponse(
            content={
                "success": True,
                "message": "文件上传成功",
                "data": {
                    "id": doc_id,
                    "filename": unique_filename,
                    "original_filename": file.filename,
                },
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@app.post("/api/documents/{doc_id}/process")
async def process_document(doc_id: int):
    """
    处理文档(解析、分块、向量化)
    """
    try:
        # 获取文档信息
        doc = DocumentDB.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 更新状态为处理中
        DocumentDB.update_document_status(doc_id, "processing")

        # 处理文档
        doc_splits, vector_ids = document_processor.process_document(
            doc["file_path"], doc["file_type"]
        )

        # 更新状态为已完成
        DocumentDB.update_document_status(doc_id, "completed", len(doc_splits))

        return JSONResponse(
            content={
                "success": True,
                "message": "文档处理成功",
                "data": {
                    "chunk_count": len(doc_splits),
                    "vector_count": len(vector_ids),
                },
            }
        )

    except Exception as e:
        DocumentDB.update_document_status(doc_id, "failed")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.get("/api/documents")
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
):
    """
    获取文档列表
    """
    try:
        documents, total = DocumentDB.list_documents(page, page_size, status)

        return JSONResponse(
            content={
                "success": True,
                "data": {
                    "list": documents,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: int):
    """
    获取文档详情
    """
    try:
        doc = DocumentDB.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        return JSONResponse(content={"success": True, "data": doc})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: int):
    """
    删除文档
    """
    try:
        # 获取文档信息
        doc = DocumentDB.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 删除文件
        file_path = Path(doc["file_path"])
        if file_path.exists():
            file_path.unlink()

        # 删除数据库记录
        DocumentDB.delete_document(doc_id)

        return JSONResponse(content={"success": True, "message": "文档删除成功"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@app.post("/api/search")
async def search_documents(request: SearchRequest):
    """
    搜索文档
    """
    try:
        results = rag_service.similarity_search_with_score(
            query=request.query, k=request.k
        )

        return JSONResponse(
            content={
                "success": True,
                "data": {"query": request.query, "results": results},
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.post("/api/question")
async def ask_question(request: QuestionRequest):
    """
    问答接口
    """
    try:
        result = rag_service.query_with_agent(request.question)

        return JSONResponse(content={"success": True, "data": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@app.get("/api/health")
async def health_check():
    """
    健康检查
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
