#!/usr/bin/env python3
"""
核心功能测试
验证重构后的RAG系统核心功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


async def test_core_functionality():
    """测试核心功能"""
    print("🚀 测试RAG系统核心功能")
    print("=" * 40)

    try:
        # 导入核心模块
        from examples.llama_rag_system_demo.rag import RAGSystem

        print("✅ 核心模块导入成功")

        # 创建RAG系统
        async with RAGSystem() as rag:
            print("✅ RAG系统初始化成功")

            # 设置向量集合
            await rag.setup_collection(overwrite=True)
            print("✅ 向量集合设置完成")

            # 添加知识
            knowledge = "人工智能是计算机科学的一个分支，致力于创建智能系统。"
            count = await rag.add_text(knowledge)
            print(f"✅ 添加知识完成，共 {count} 个文档块")

            # 测试问答
            answer = await rag.chat("什么是人工智能？")
            print(f"✅ 问答测试成功")
            print(f"💡 回答: {answer}")

            print("\n🎉 核心功能测试完成！")
            return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_core_functionality())
    sys.exit(0 if success else 1)
