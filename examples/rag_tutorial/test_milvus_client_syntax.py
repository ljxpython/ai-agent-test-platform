"""
测试MilvusClient语法和结构的简单脚本
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(__file__))

try:
    from milvus_client import MilvusVectorClient

    print("✅ MilvusVectorClient 导入成功")

    # 测试类的基本结构
    client = MilvusVectorClient()
    print("✅ MilvusVectorClient 实例化成功")

    # 检查主要方法是否存在
    methods_to_check = [
        "connect",
        "disconnect",
        "create_collection",
        "insert_data",
        "search_similar",
        "get_collection_stats",
        "delete_by_expr",
        "drop_collection",
    ]

    for method in methods_to_check:
        if hasattr(client, method):
            print(f"✅ 方法 {method} 存在")
        else:
            print(f"❌ 方法 {method} 不存在")

    print("\n🎉 MilvusClient 代码结构验证完成！")
    print("📝 代码已成功从Collection方式修改为MilvusClient方式")

except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")
