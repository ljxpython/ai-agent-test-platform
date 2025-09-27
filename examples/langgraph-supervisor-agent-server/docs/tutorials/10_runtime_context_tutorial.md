# 10. 运行时上下文教学

## 🎯 学习目标

通过这个教程，你将学会：
- 运行时上下文的概念和用途
- 如何在节点间传递上下文信息
- 上下文的生命周期管理
- 实际应用场景和最佳实践

## 📚 核心概念

### 1. 什么是运行时上下文？

运行时上下文是在图执行过程中**传递额外信息**的机制，不属于状态但影响执行行为：

```python
def node_function(state: State, *, context: Context) -> State:
    # 使用上下文信息
    user_id = context.user_id
    language = context.language
    # 执行逻辑...
```

**上下文 vs 状态：**
- **状态**：图执行的数据流，会被保存和传递
- **上下文**：执行环境信息，如用户ID、语言、权限等

### 2. 上下文类型

```python
from dataclasses import dataclass

@dataclass
class Context:
    user_id: str
    language: str = "zh"
    model_name: str = "deepseek-chat"
    permissions: list = None

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []
```

### 3. 上下文传递

上下文通过 `context` 参数传递给节点：

```python
def personalized_greeting(state: State, *, context: Context) -> State:
    """生成个性化问候"""
    user_id = context.user_id
    language = context.language

    # 根据上下文生成个性化内容
    if language == "zh":
        greeting = f"你好！用户 {user_id}"
    else:
        greeting = f"Hello! User {user_id}"

    return {"messages": [{"role": "assistant", "content": greeting}]}
```

## 🔍 代码详细解析

### 基础上下文设置

```python
from dataclasses import dataclass
from langgraph.store.memory import InMemoryStore

@dataclass
class Context:
    user_id: str
    language: str = "zh"
    model_name: str = "deepseek-chat"

# 创建内存存储
store = InMemoryStore()

# 预填充一些用户数据
store.put(("users",), "user_123", {"name": "张三", "age": 25, "city": "北京"})
store.put(("users",), "user_456", {"name": "李四", "age": 30, "city": "上海"})
store.put(("preferences",), "user_123", {"theme": "dark", "language": "zh"})

def personalized_greeting(state: State, *, store: InMemoryStore, context: Context) -> State:
    """生成个性化问候"""
    user_id = context.user_id
    language = context.language

    # 从存储中获取用户信息
    user_info = None
    if store:
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

    return {"messages": [{"role": "assistant", "content": greeting}]}
```

### 上下文感知处理

```python
def context_aware_chat(state: State, *, store: InMemoryStore, context: Context) -> State:
    """上下文感知的聊天"""
    user_id = context.user_id
    language = context.language

    # 获取用户偏好
    preferences = None
    if store:
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
    messages = state["messages"]
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}

# 构建图
graph = (
    StateGraph(state_schema=State)
    .add_node("greeting", personalized_greeting)
    .add_node("chat", context_aware_chat)
    .add_edge(START, "greeting")
    .add_edge("greeting", "chat")
    .add_edge("chat", END)
    .compile(store=store)
)
```

### 运行时上下文演示

```python
def run_runtime_context_demo():
    """运行运行时上下文演示"""
    print("运行时上下文演示启动！")

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
            result = graph.invoke({}, context=Context(**context_data))
            print(f"回复: {result['messages'][-1].content}")
        except Exception as e:
            print(f"错误: {e}")
```

## 🚀 高级上下文管理

### 1. 动态上下文

```python
@dataclass
class DynamicContext:
    user_id: str
    session_id: str
    language: str = "zh"
    timezone: str = "Asia/Shanghai"
    device_type: str = "web"
    request_time: datetime.datetime = None

    def __post_init__(self):
        if self.request_time is None:
            self.request_time = datetime.datetime.now()

    def is_business_hours(self) -> bool:
        """检查是否在工作时间"""
        hour = self.request_time.hour
        return 9 <= hour <= 18

    def get_greeting_style(self) -> str:
        """根据时间获取问候风格"""
        hour = self.request_time.hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        else:
            return "evening"

def time_aware_processor(state: State, *, context: DynamicContext) -> State:
    """时间感知处理器"""
    greeting_style = context.get_greeting_style()
    is_business = context.is_business_hours()

    if context.language == "zh":
        if greeting_style == "morning":
            greeting = "早上好！"
        elif greeting_style == "afternoon":
            greeting = "下午好！"
        else:
            greeting = "晚上好！"
    else:
        if greeting_style == "morning":
            greeting = "Good morning!"
        elif greeting_style == "afternoon":
            greeting = "Good afternoon!"
        else:
            greeting = "Good evening!"

    if not is_business:
        if context.language == "zh":
            greeting += " 现在是非工作时间，回复可能会有延迟。"
        else:
            greeting += " It's outside business hours, responses may be delayed."

    return {"messages": [{"role": "assistant", "content": greeting}]}
```

### 2. 权限上下文

```python
@dataclass
class PermissionContext:
    user_id: str
    role: str = "user"
    permissions: list = None
    security_level: int = 1

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = self._get_default_permissions()

    def _get_default_permissions(self) -> list:
        """获取默认权限"""
        role_permissions = {
            "admin": ["read", "write", "delete", "manage"],
            "moderator": ["read", "write", "moderate"],
            "user": ["read"],
            "guest": []
        }
        return role_permissions.get(self.role, [])

    def has_permission(self, permission: str) -> bool:
        """检查权限"""
        return permission in self.permissions

    def can_access_sensitive_data(self) -> bool:
        """检查是否可以访问敏感数据"""
        return self.security_level >= 3 and self.has_permission("read")

def permission_aware_processor(state: State, *, context: PermissionContext) -> State:
    """权限感知处理器"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    user_content = last_message.content.lower()

    # 检查敏感操作
    sensitive_operations = ["删除", "重置", "管理", "配置"]

    if any(op in user_content for op in sensitive_operations):
        if not context.has_permission("write"):
            response = "抱歉，您没有执行此操作的权限。"
            return {"messages": [{"role": "assistant", "content": response}]}

    # 检查敏感数据访问
    sensitive_data_keywords = ["用户列表", "系统信息", "日志"]

    if any(keyword in user_content for keyword in sensitive_data_keywords):
        if not context.can_access_sensitive_data():
            response = "抱歉，您的安全级别不足以访问此信息。"
            return {"messages": [{"role": "assistant", "content": response}]}

    # 正常处理
    response = f"[{context.role}] 正在处理您的请求..."
    return {"messages": [{"role": "assistant", "content": response}]}
```

### 3. 多租户上下文

```python
@dataclass
class TenantContext:
    tenant_id: str
    user_id: str
    organization: str
    subscription_tier: str = "basic"
    feature_flags: dict = None

    def __post_init__(self):
        if self.feature_flags is None:
            self.feature_flags = self._get_default_features()

    def _get_default_features(self) -> dict:
        """获取默认功能标志"""
        tier_features = {
            "basic": {"ai_chat": True, "file_upload": False, "api_access": False},
            "pro": {"ai_chat": True, "file_upload": True, "api_access": True},
            "enterprise": {"ai_chat": True, "file_upload": True, "api_access": True, "custom_models": True}
        }
        return tier_features.get(self.subscription_tier, {})

    def has_feature(self, feature: str) -> bool:
        """检查功能是否可用"""
        return self.feature_flags.get(feature, False)

    def get_rate_limit(self) -> int:
        """获取速率限制"""
        limits = {
            "basic": 10,
            "pro": 100,
            "enterprise": 1000
        }
        return limits.get(self.subscription_tier, 5)

def tenant_aware_processor(state: State, *, context: TenantContext) -> State:
    """多租户感知处理器"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    user_content = last_message.content.lower()

    # 检查功能可用性
    if "上传文件" in user_content:
        if not context.has_feature("file_upload"):
            response = f"文件上传功能需要 Pro 或 Enterprise 订阅。当前订阅：{context.subscription_tier}"
            return {"messages": [{"role": "assistant", "content": response}]}

    if "api" in user_content:
        if not context.has_feature("api_access"):
            response = f"API 访问需要 Pro 或 Enterprise 订阅。当前订阅：{context.subscription_tier}"
            return {"messages": [{"role": "assistant", "content": response}]}

    # 添加租户信息到回复
    response = f"[{context.organization}] 正在为您处理请求..."
    return {"messages": [{"role": "assistant", "content": response}]}
```

## 🎯 实践练习

### 练习1：国际化上下文

```python
@dataclass
class I18nContext:
    user_id: str
    language: str = "zh"
    country: str = "CN"
    timezone: str = "Asia/Shanghai"
    currency: str = "CNY"

    def get_localized_message(self, key: str) -> str:
        """获取本地化消息"""
        messages = {
            "zh": {
                "welcome": "欢迎使用我们的服务！",
                "goodbye": "再见，期待下次见面！",
                "error": "抱歉，发生了错误。"
            },
            "en": {
                "welcome": "Welcome to our service!",
                "goodbye": "Goodbye, see you next time!",
                "error": "Sorry, an error occurred."
            }
        }

        return messages.get(self.language, {}).get(key, key)

    def format_currency(self, amount: float) -> str:
        """格式化货币"""
        currency_symbols = {
            "CNY": "¥",
            "USD": "$",
            "EUR": "€"
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        return f"{symbol}{amount:.2f}"

def i18n_processor(state: State, *, context: I18nContext) -> State:
    """国际化处理器"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        welcome_msg = context.get_localized_message("welcome")
        return {"messages": [{"role": "assistant", "content": welcome_msg}]}

    user_content = last_message.content.lower()

    # 处理货币相关请求
    if "价格" in user_content or "price" in user_content:
        price = 99.99
        formatted_price = context.format_currency(price)

        if context.language == "zh":
            response = f"价格是 {formatted_price}"
        else:
            response = f"The price is {formatted_price}"

        return {"messages": [{"role": "assistant", "content": response}]}

    # 处理时间相关请求
    if "时间" in user_content or "time" in user_content:
        import pytz
        try:
            tz = pytz.timezone(context.timezone)
            current_time = datetime.datetime.now(tz)

            if context.language == "zh":
                response = f"当前时间是 {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                response = f"Current time is {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
        except:
            response = context.get_localized_message("error")

        return {"messages": [{"role": "assistant", "content": response}]}

    # 默认回复
    response = "我明白了。" if context.language == "zh" else "I understand."
    return {"messages": [{"role": "assistant", "content": response}]}
```

### 练习2：性能监控上下文

```python
@dataclass
class PerformanceContext:
    request_id: str
    start_time: datetime.datetime = None
    max_execution_time: float = 30.0
    enable_profiling: bool = False

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.datetime.now()

    def get_elapsed_time(self) -> float:
        """获取已用时间"""
        return (datetime.datetime.now() - self.start_time).total_seconds()

    def is_timeout(self) -> bool:
        """检查是否超时"""
        return self.get_elapsed_time() > self.max_execution_time

    def log_performance(self, step_name: str):
        """记录性能信息"""
        if self.enable_profiling:
            elapsed = self.get_elapsed_time()
            print(f"[{self.request_id}] {step_name}: {elapsed:.3f}s")

def performance_aware_processor(state: State, *, context: PerformanceContext) -> State:
    """性能感知处理器"""
    context.log_performance("processor_start")

    # 检查超时
    if context.is_timeout():
        response = "请求处理超时，请稍后重试。"
        return {"messages": [{"role": "assistant", "content": response}]}

    # 模拟处理时间
    import time
    time.sleep(0.1)

    context.log_performance("processing_complete")

    elapsed = context.get_elapsed_time()
    response = f"处理完成，用时 {elapsed:.3f} 秒"

    return {"messages": [{"role": "assistant", "content": response}]}
```

### 练习3：安全上下文

```python
@dataclass
class SecurityContext:
    user_id: str
    ip_address: str
    user_agent: str
    session_token: str
    security_level: int = 1

    def is_trusted_ip(self) -> bool:
        """检查是否为可信IP"""
        trusted_ips = ["127.0.0.1", "192.168.1.0/24"]
        # 简化实现
        return self.ip_address.startswith("192.168.") or self.ip_address == "127.0.0.1"

    def validate_session(self) -> bool:
        """验证会话"""
        # 简化实现
        return len(self.session_token) > 10

    def detect_suspicious_activity(self, content: str) -> bool:
        """检测可疑活动"""
        suspicious_patterns = ["script", "eval", "exec", "system"]
        return any(pattern in content.lower() for pattern in suspicious_patterns)

def security_aware_processor(state: State, *, context: SecurityContext) -> State:
    """安全感知处理器"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    user_content = last_message.content

    # 验证会话
    if not context.validate_session():
        response = "会话无效，请重新登录。"
        return {"messages": [{"role": "assistant", "content": response}]}

    # 检查可疑活动
    if context.detect_suspicious_activity(user_content):
        response = "检测到可疑活动，请求已被阻止。"
        print(f"安全警告: 用户 {context.user_id} 从 {context.ip_address} 发送可疑内容")
        return {"messages": [{"role": "assistant", "content": response}]}

    # 检查IP信任度
    if not context.is_trusted_ip() and context.security_level < 2:
        response = "来自不可信网络的请求需要额外验证。"
        return {"messages": [{"role": "assistant", "content": response}]}

    # 正常处理
    response = f"安全验证通过，正在处理您的请求..."
    return {"messages": [{"role": "assistant", "content": response}]}
```

## 🔧 常见问题

### Q1: 上下文和状态有什么区别？

**答：**
- **状态**：图执行的数据流，会被持久化和传递
- **上下文**：执行环境信息，不会被持久化，每次调用时提供

```python
# 状态：会被保存和传递
state = {"messages": [...], "user_data": {...}}

# 上下文：执行时的环境信息
context = Context(user_id="123", language="zh")
```

### Q2: 如何在上下文中传递复杂对象？

**答：** 使用数据类和类型注解：

```python
@dataclass
class ComplexContext:
    user_profile: dict
    database_connection: object
    cache_client: object

    def get_user_setting(self, key: str):
        return self.user_profile.get("settings", {}).get(key)
```

### Q3: 上下文可以修改吗？

**答：** 可以修改，但要注意线程安全：

```python
@dataclass
class MutableContext:
    user_id: str
    request_count: int = 0

    def increment_request(self):
        self.request_count += 1

def counting_processor(state: State, *, context: MutableContext) -> State:
    context.increment_request()
    response = f"这是第 {context.request_count} 个请求"
    return {"messages": [{"role": "assistant", "content": response}]}
```

## 📖 相关资源

### 官方文档
- [LangGraph 运行时上下文](https://langchain-ai.github.io/langgraph/concepts/low_level/#context)
- [存储和上下文](https://langchain-ai.github.io/langgraph/concepts/persistence/#store)

### 下一步学习
- [11. 短期记忆教学](11_short_term_memory_tutorial.md) - 记忆管理
- [05. 状态管理教学](05_state_management_tutorial.md) - 状态设计

### 代码示例
- 完整代码：[10_runtime_context.py](../../teach_code/10_runtime_context.py)
- 运行方式：`python teach_code/10_runtime_context.py`

## 🌟 总结

运行时上下文是构建灵活应用的重要机制：

1. **环境信息**：传递用户、权限、配置等信息
2. **个性化**：根据上下文提供定制化服务
3. **安全控制**：实现权限检查和安全验证
4. **多租户**：支持多组织、多用户隔离
5. **国际化**：提供本地化和多语言支持

掌握运行时上下文后，你可以构建更智能、更安全的应用！
