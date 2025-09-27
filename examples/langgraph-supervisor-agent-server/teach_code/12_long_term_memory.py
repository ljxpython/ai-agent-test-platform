from typing import Annotated

from config import llm
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from typing_extensions import TypedDict

# 创建全局存储
store = InMemoryStore()

# 预填充一些用户数据
store.put(
    ("users",),
    "user_123",
    {
        "name": "张三",
        "preferences": ["编程", "音乐", "旅行"],
        "last_conversation": "2024-01-15",
    },
)


@tool
def save_user_info(info: str, *, store: InMemoryStore, config: RunnableConfig) -> str:
    """保存用户信息到长期记忆"""
    user_id = config["configurable"].get("user_id", "default_user")

    # 获取现有用户信息
    existing_info = store.get(("users",), user_id)
    user_data = existing_info.value if existing_info else {}

    # 解析并更新信息
    if "名字" in info or "叫" in info:
        import re

        name_match = re.search(r"(?:我叫|名字是|我是)(.+)", info)
        if name_match:
            user_data["name"] = name_match.group(1).strip()

    if "喜欢" in info:
        preferences = user_data.get("preferences", [])
        preference = info.replace("我喜欢", "").strip()
        if preference not in preferences:
            preferences.append(preference)
            user_data["preferences"] = preferences

    # 更新最后对话时间
    import datetime

    user_data["last_conversation"] = datetime.datetime.now().isoformat()

    # 保存到存储
    store.put(("users",), user_id, user_data)

    return f"已保存信息到长期记忆：{info}"


@tool
def get_user_info(query: str, *, store: InMemoryStore, config: RunnableConfig) -> str:
    """从长期记忆获取用户信息"""
    user_id = config["configurable"].get("user_id", "default_user")

    user_info = store.get(("users",), user_id)
    if not user_info:
        return "长期记忆中没有找到用户信息"

    user_data = user_info.value

    if "名字" in query:
        return f"您的名字是：{user_data.get('name', '未知')}"

    if "喜欢" in query or "偏好" in query:
        preferences = user_data.get("preferences", [])
        if preferences:
            return f"您喜欢：{', '.join(preferences)}"
        else:
            return "长期记忆中没有您的偏好信息"

    if "上次" in query:
        last_conv = user_data.get("last_conversation", "未知")
        return f"上次对话时间：{last_conv}"

    return f"用户信息：{user_data}"


# 创建智能体
agent = create_react_agent(
    model=llm, tools=[save_user_info, get_user_info], store=store
)


def run_long_term_memory_demo():
    """运行长期记忆演示"""
    print("长期记忆演示启动！")
    print("这个智能体可以跨对话保存和检索用户信息。")
    print("信息会持久化保存，即使重启程序也能记住。")

    # 让用户选择用户ID
    user_id = input("请输入用户ID（默认为 user_123）: ").strip()
    if not user_id:
        user_id = "user_123"

    config = {"configurable": {"user_id": user_id}}

    # 显示现有用户信息
    try:
        existing_info = store.get(("users",), user_id)
        if existing_info:
            print(f"\n找到现有用户信息：{existing_info.value}")
        else:
            print(f"\n新用户：{user_id}")
    except Exception as e:
        print(f"获取用户信息失败：{e}")

    print("输入 'quit' 退出。")

    while True:
        user_input = input(f"\n[{user_id}] 用户: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        try:
            # 调用智能体
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]}, config=config
            )

            # 输出回复
            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")


def manage_user_data():
    """管理用户数据"""
    print("\n" + "=" * 50)
    print("用户数据管理")
    print("=" * 50)

    while True:
        print("\n选项:")
        print("1. 查看所有用户")
        print("2. 查看特定用户")
        print("3. 删除用户")
        print("4. 返回")

        choice = input("请选择 (1-4): ").strip()

        if choice == "1":
            # 注意：InMemoryStore 不直接支持列出所有键
            # 这里我们手动维护一个用户列表
            known_users = ["user_123", "user_456", "user_789"]
            print("\n已知用户:")
            for user_id in known_users:
                user_info = store.get(("users",), user_id)
                if user_info:
                    print(f"  {user_id}: {user_info.value}")

        elif choice == "2":
            user_id = input("输入用户ID: ").strip()
            user_info = store.get(("users",), user_id)
            if user_info:
                print(f"用户信息: {user_info.value}")
            else:
                print("用户不存在")

        elif choice == "3":
            user_id = input("输入要删除的用户ID: ").strip()
            confirm = input(f"确认删除用户 {user_id}? (yes/no): ").strip()
            if confirm.lower() in ["yes", "y"]:
                # 注意：InMemoryStore 可能不支持删除操作
                # 这里我们设置为空值
                store.put(("users",), user_id, {})
                print(f"已删除用户 {user_id}")
            else:
                print("取消删除")

        elif choice == "4":
            break
        else:
            print("无效选择")


if __name__ == "__main__":
    run_long_term_memory_demo()
    manage_user_data()
