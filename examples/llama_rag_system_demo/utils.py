"""
工具模块
提供通用的工具函数和路径设置
"""

import sys
from pathlib import Path


def setup_project_path():
    """设置项目路径，确保可以导入项目模块"""
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# 自动设置路径
setup_project_path()
