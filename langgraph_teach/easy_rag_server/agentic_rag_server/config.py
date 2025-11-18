"""
配置文件
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 基础路径
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 向量数据库配置
MILVUS_URI = os.getenv("MILVUS_URI", "http://{ip}:19530")
MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "LangChainCollection")

# Embedding模型配置
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "http://{ip}:11434")

# 文档处理配置
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1024"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# 文件上传配置
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".doc", ".docx"}

# CORS配置
CORS_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
]
