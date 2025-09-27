from dataclasses import dataclass
from typing import TypedDict

from config import llm
from langgraph.graph import END, START, StateGraph
from langgraph.store.memory import InMemoryStore


@dataclass
class Context:
    user_id: str
    language: str = "zh"
    model_name: str = "deepseek-chat"


class State(TypedDict):
    response: str
    context: Context
    user_input: str


# 创建内存存储
store = InMemoryStore()

# 预填充一些用户数据
store.put(("users",), "user_123", {"name": "张三", "age": 25, "city": "北京"})
store.put(("users",), "user_456", {"name": "李四", "age": 30, "city": "上海"})
store.put(("preferences",), "user_123", {"theme": "dark", "language": "zh"})


def personalized_greeting(state: State) -> State:
    """生成个性化问候"""
    # 从状态中获取上下文信息
    context = state.get("context")
    if not context:
        return {"response": "你好！欢迎使用我们的服务。"}

    user_id = context.user_id
    language = context.language

    # 从全局存储中获取用户信息
    user_info = None
    user_memory = store.get(("users",), user_id)
    if user_memory:
        user_info = user_memory.value

    # 生成个性化问候
    if user_info:
        name = user_info.get("name", "用户")
        city = user_info.get("city", "")
        if language == "zh":
            greeting = f"你好 {name}！很高兴再次见到你。"
            if city:
                greeting += f" 希望{city}的天气不错。"
        else:
            greeting = f"Hello {name}! Nice to see you again."
            if city:
                greeting += f" Hope the weather in {city} is nice."
    else:
        if language == "zh":
            greeting = "你好！欢迎使用我们的服务。"
        else:
            greeting = "Hello! Welcome to our service."

    return {"response": greeting}


def context_aware_chat(state: State) -> State:
    """上下文感知的聊天"""
    # 从状态中获取上下文信息
    context = state.get("context")
    if not context:
        return {"response": "抱歉，无法获取上下文信息。"}

    user_id = context.user_id
    language = context.language
    user_input = state.get("user_input", "")

    # 获取用户偏好
    preferences = None
    pref_memory = store.get(("preferences",), user_id)
    if pref_memory:
        preferences = pref_memory.value

    # 构建系统提示
    system_prompt = "你是一个有用的助手。"
    if language == "zh":
        system_prompt = "你是一个有用的中文助手。请用中文回复。"
    else:
        system_prompt = "You are a helpful assistant. Please reply in English."

    if preferences:
        theme = preferences.get("theme", "light")
        system_prompt += f" 用户偏好{theme}主题。"

    # 生成回复
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    response = llm.invoke(messages)

    return {"response": response.content}


# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("greeting", personalized_greeting)
graph_builder.add_node("chat", context_aware_chat)
graph_builder.add_edge(START, "greeting")
graph_builder.add_edge("greeting", "chat")
graph_builder.add_edge("chat", END)

# 编译图
graph = graph_builder.compile()


def run_runtime_context_demo():
    """运行运行时上下文演示"""
    print("运行时上下文演示启动！")
    print("这个演示展示如何使用运行时上下文和存储。")

    # 测试不同的用户和语言
    test_cases = [
        {"user_id": "user_123", "language": "zh"},
        {"user_id": "user_456", "language": "zh"},
        {"user_id": "user_789", "language": "en"},  # 不存在的用户
    ]

    for i, context_data in enumerate(test_cases, 1):
        print(f"\n=== 测试案例 {i} ===")
        print(f"用户ID: {context_data['user_id']}")
        print(f"语言: {context_data['language']}")

        try:
            # 将上下文信息作为状态的一部分传递
            context_obj = Context(**context_data)
            result = graph.invoke(
                {"context": context_obj, "user_input": "你好，请介绍一下你的功能"}
            )
            print(f"回复: {result['response']}")
        except Exception as e:
            print(f"错误: {e}")


def interactive_context_demo():
    """交互式上下文演示"""
    print("\n" + "=" * 50)
    print("交互式运行时上下文演示")
    print("=" * 50)

    while True:
        print("\n选项:")
        print("1. 测试个性化问候")
        print("2. 添加新用户")
        print("3. 查看用户信息")
        print("4. 更新用户偏好")
        print("5. 退出")

        choice = input("请选择 (1-5): ").strip()

        if choice == "1":
            user_id = input("输入用户ID: ").strip()
            language = input("输入语言 (zh/en): ").strip() or "zh"

            try:
                context_obj = Context(user_id=user_id, language=language)
                result = graph.invoke({"context": context_obj, "user_input": "你好"})
                print(f"问候: {result['response']}")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "2":
            user_id = input("输入新用户ID: ").strip()
            name = input("输入姓名: ").strip()
            city = input("输入城市: ").strip()

            if user_id and name:
                store.put(("users",), user_id, {"name": name, "city": city})
                print(f"已添加用户: {user_id}")
            else:
                print("用户ID和姓名不能为空")

        elif choice == "3":
            user_id = input("输入用户ID: ").strip()

            user_memory = store.get(("users",), user_id)
            if user_memory:
                print(f"用户信息: {user_memory.value}")
            else:
                print("用户不存在")

            pref_memory = store.get(("preferences",), user_id)
            if pref_memory:
                print(f"用户偏好: {pref_memory.value}")
            else:
                print("无偏好设置")

        elif choice == "4":
            user_id = input("输入用户ID: ").strip()
            theme = input("输入主题 (light/dark): ").strip()
            language = input("输入语言 (zh/en): ").strip()

            preferences = {}
            if theme:
                preferences["theme"] = theme
            if language:
                preferences["language"] = language

            if preferences:
                store.put(("preferences",), user_id, preferences)
                print(f"已更新用户 {user_id} 的偏好")
            else:
                print("没有提供偏好设置")

        elif choice == "5":
            print("退出")
            break
        else:
            print("无效选择")


def advanced_context_demo():
    """高级上下文演示"""
    print("\n" + "=" * 50)
    print("高级上下文演示")
    print("=" * 50)

    # 创建更复杂的上下文
    @dataclass
    class AdvancedContext:
        user_id: str
        session_id: str
        language: str = "zh"
        timezone: str = "Asia/Shanghai"
        device_type: str = "web"

    class AdvancedState(TypedDict):
        user_input: str
        response: str
        metadata: dict

    def advanced_processor(
        state: AdvancedState, *, store: InMemoryStore, context: AdvancedContext
    ) -> AdvancedState:
        """高级上下文处理器"""
        user_input = state.get("user_input", "")

        # 获取用户信息
        user_info = store.get(("users",), context.user_id)
        session_info = store.get(("sessions",), context.session_id)

        # 构建元数据
        metadata = {
            "user_id": context.user_id,
            "session_id": context.session_id,
            "language": context.language,
            "timezone": context.timezone,
            "device_type": context.device_type,
            "has_user_info": user_info is not None,
            "has_session_info": session_info is not None,
        }

        # 生成响应
        if context.language == "zh":
            response = f"收到来自{context.device_type}设备的消息: {user_input}"
        else:
            response = (
                f"Received message from {context.device_type} device: {user_input}"
            )

        return {"response": response, "metadata": metadata}

    # 构建高级图
    advanced_graph = (
        StateGraph(state_schema=AdvancedState)
        .add_node("process", advanced_processor)
        .add_edge(START, "process")
        .add_edge("process", END)
        .compile(store=store)
    )

    # 测试高级上下文
    test_contexts = [
        AdvancedContext(
            user_id="user_123",
            session_id="session_001",
            language="zh",
            device_type="mobile",
        ),
        AdvancedContext(
            user_id="user_456",
            session_id="session_002",
            language="en",
            device_type="desktop",
        ),
    ]

    for i, ctx in enumerate(test_contexts, 1):
        print(f"\n=== 高级测试 {i} ===")

        result = advanced_graph.invoke({"user_input": f"测试消息 {i}"}, context=ctx)

        print(f"响应: {result['response']}")
        print(f"元数据: {result['metadata']}")


def context_inheritance_demo():
    """上下文继承演示"""
    print("\n" + "=" * 50)
    print("上下文继承演示")
    print("=" * 50)

    # 演示如何在不同节点间传递和修改上下文
    @dataclass
    class MutableContext:
        user_id: str
        step_count: int = 0
        processing_flags: dict = None

        def __post_init__(self):
            if self.processing_flags is None:
                self.processing_flags = {}

    class StepState(TypedDict):
        step_name: str
        result: str

    def step_a(state: StepState, *, context: MutableContext) -> StepState:
        """步骤A"""
        context.step_count += 1
        context.processing_flags["step_a_completed"] = True

        return {"step_name": "A", "result": f"步骤A完成 (总步骤: {context.step_count})"}

    def step_b(state: StepState, *, context: MutableContext) -> StepState:
        """步骤B"""
        context.step_count += 1
        context.processing_flags["step_b_completed"] = True

        # 检查前置条件
        if context.processing_flags.get("step_a_completed"):
            result = f"步骤B完成 (总步骤: {context.step_count}, A已完成)"
        else:
            result = f"步骤B完成 (总步骤: {context.step_count}, A未完成)"

        return {"step_name": "B", "result": result}

    # 构建步骤图
    step_graph = (
        StateGraph(state_schema=StepState)
        .add_node("step_a", step_a)
        .add_node("step_b", step_b)
        .add_edge(START, "step_a")
        .add_edge("step_a", "step_b")
        .add_edge("step_b", END)
        .compile()
    )

    # 测试上下文继承
    ctx = MutableContext(user_id="test_user")
    print(f"初始上下文: 步骤数={ctx.step_count}, 标志={ctx.processing_flags}")

    result = step_graph.invoke({}, context=ctx)

    print(f"最终结果: {result}")
    print(f"最终上下文: 步骤数={ctx.step_count}, 标志={ctx.processing_flags}")


if __name__ == "__main__":
    run_runtime_context_demo()
    interactive_context_demo()
    advanced_context_demo()
    context_inheritance_demo()
