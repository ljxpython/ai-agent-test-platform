"""
启动知识库管理系统后端服务
"""

import os
import sys
from pathlib import Path

# 添加父目录到路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print("知识库管理系统后端服务")
    print("=" * 60)
    print("API文档: http://localhost:8002/docs")
    print("健康检查: http://localhost:8002/api/health")
    print("=" * 60)

    # 切换到父目录作为工作目录
    os.chdir(str(parent_dir))

    uvicorn.run(
        "agentic_rag_server.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info",
    )
