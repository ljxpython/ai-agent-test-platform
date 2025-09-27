#!/usr/bin/env python3
"""
LangGraph 示例运行器
用于测试和演示所有 LangGraph 教程示例
"""

import importlib.util
import os
import sys
from pathlib import Path


def load_module_from_file(file_path):
    """从文件路径加载模块"""
    spec = importlib.util.spec_from_file_location("module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_environment():
    """检查环境配置"""
    print("🔍 检查环境配置...")

    required_vars = ["OPENAI_API_KEY"]
    optional_vars = ["DEEPSEEK_API_KEY", "TAVILY_API_KEY"]

    missing_required = []
    missing_optional = []

    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)

    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)

    if missing_required:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_required)}")
        print("请在 .env 文件中配置这些变量")
        return False

    if missing_optional:
        print(f"⚠️  缺少可选的环境变量: {', '.join(missing_optional)}")
        print("某些功能可能不可用")

    print("✅ 环境配置检查完成")
    return True


def list_examples():
    """列出所有示例"""
    examples = [
        ("01_basic_chatbot.py", "基础聊天机器人"),
        ("02_streaming_chatbot.py", "流式聊天机器人"),
        ("03_chatbot_with_tools.py", "带搜索工具的聊天机器人"),
        ("04_custom_tools.py", "自定义工具集成"),
        ("05_state_management.py", "复杂状态管理"),
        ("06_memory_checkpoint.py", "内存检查点"),
        ("07_sqlite_checkpoint.py", "SQLite 检查点"),
        ("08_human_in_the_loop.py", "人机交互"),
        ("09_time_travel.py", "时间旅行"),
        ("10_runtime_context.py", "运行时上下文"),
        ("11_short_term_memory.py", "短期记忆"),
        ("12_long_term_memory.py", "长期记忆"),
        ("13_subgraphs.py", "基础子图"),
        ("14_subgraph_with_memory.py", "带独立内存的子图"),
        ("15_mcp_integration.py", "MCP 客户端集成"),
        ("16_custom_mcp_server.py", "自定义 MCP 服务器"),
        ("17_multi_agent_supervisor.py", "Supervisor 模式多智能体"),
    ]

    print("\n📚 可用的示例:")
    for i, (filename, description) in enumerate(examples, 1):
        status = "✅" if Path(filename).exists() else "❌"
        print(f"{i:2d}. {status} {filename:<30} - {description}")

    return examples


def run_example(filename):
    """运行指定示例"""
    if not Path(filename).exists():
        print(f"❌ 文件不存在: {filename}")
        return False

    print(f"\n🚀 运行示例: {filename}")
    print("=" * 60)

    try:
        # 导入并运行模块
        module = load_module_from_file(filename)

        # 检查是否有 main 函数
        if hasattr(module, "__main__") and callable(getattr(module, "__main__")):
            module.__main__()
        else:
            print("✅ 模块加载成功（无 main 函数）")

        return True

    except KeyboardInterrupt:
        print("\n⏹️  用户中断")
        return True
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        return False


def test_imports():
    """测试所有必需的导入"""
    print("\n🧪 测试导入...")

    imports_to_test = [
        ("langgraph", "LangGraph 核心"),
        ("langchain", "LangChain 核心"),
        ("langchain_core", "LangChain 核心组件"),
        ("typing_extensions", "类型扩展"),
        ("dotenv", "环境变量"),
    ]

    optional_imports = [
        ("langchain_deepseek", "DeepSeek 集成"),
        ("langchain_openai", "OpenAI 集成"),
        ("langchain_tavily", "Tavily 搜索"),
        ("langchain_mcp_adapters", "MCP 适配器"),
    ]

    success_count = 0
    total_count = len(imports_to_test) + len(optional_imports)

    # 测试必需导入
    for module_name, description in imports_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name:<25} - {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module_name:<25} - {description} (错误: {e})")

    # 测试可选导入
    for module_name, description in optional_imports:
        try:
            __import__(module_name)
            print(f"✅ {module_name:<25} - {description}")
            success_count += 1
        except ImportError:
            print(f"⚠️  {module_name:<25} - {description} (可选)")
            success_count += 0.5  # 可选导入算半分

    print(f"\n导入测试完成: {success_count}/{total_count}")
    return success_count >= len(imports_to_test)


def interactive_menu():
    """交互式菜单"""
    examples = list_examples()

    while True:
        print("\n" + "=" * 60)
        print("🎯 LangGraph 示例运行器")
        print("=" * 60)
        print("选项:")
        print("  0. 退出")
        print("  1. 检查环境")
        print("  2. 测试导入")
        print("  3. 列出所有示例")
        print("  4-20. 运行指定示例")
        print("  99. 运行所有示例（仅加载测试）")

        try:
            choice = input("\n请选择 (0-99): ").strip()

            if choice == "0":
                print("👋 再见！")
                break
            elif choice == "1":
                check_environment()
            elif choice == "2":
                test_imports()
            elif choice == "3":
                list_examples()
            elif choice == "99":
                print("\n🧪 运行所有示例（仅加载测试）...")
                for filename, description in examples:
                    if Path(filename).exists():
                        try:
                            load_module_from_file(filename)
                            print(f"✅ {filename} - 加载成功")
                        except Exception as e:
                            print(f"❌ {filename} - 加载失败: {e}")
            elif choice.isdigit():
                index = int(choice) - 4
                if 0 <= index < len(examples):
                    filename, description = examples[index]
                    print(f"\n选择的示例: {description}")
                    confirm = input("确认运行? (y/N): ").strip().lower()
                    if confirm in ["y", "yes"]:
                        run_example(filename)
                else:
                    print("❌ 无效的示例编号")
            else:
                print("❌ 无效的选择")

        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


def main():
    """主函数"""
    print("🎯 LangGraph 实战教程示例运行器")
    print("=" * 60)

    # 检查当前目录
    if not Path("config.py").exists():
        print("❌ 请在 teach_code 目录中运行此脚本")
        sys.exit(1)

    # 检查环境
    if not check_environment():
        print("❌ 环境配置不完整，某些示例可能无法运行")
        print("请配置 .env 文件后重试")

    # 测试导入
    if not test_imports():
        print("❌ 导入测试失败，请安装必需的依赖")
        print("运行: pip install -r requirements.txt")

    # 启动交互式菜单
    interactive_menu()


if __name__ == "__main__":
    main()
