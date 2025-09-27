# 05. 状态管理教学

## 🎯 学习目标

通过这个教程，你将学会：
- 复杂状态结构的设计原则
- 状态合并策略和操作符
- 多字段状态的协调管理
- 状态验证和一致性保证

## 📚 核心概念

### 1. 什么是复杂状态管理？

复杂状态管理是指处理包含**多个字段、不同数据类型、复杂关系**的状态结构：

```python
class ComplexState(TypedDict):
    # 消息历史
    messages: Annotated[list, add_messages]

    # 用户信息
    user_name: Optional[str]
    user_preferences: dict

    # 对话统计
    message_count: Annotated[int, operator.add]

    # 上下文信息
    current_topic: Optional[str]
    conversation_summary: str
```

**复杂状态的特点：**
- **多数据类型**：字符串、数字、列表、字典
- **可选字段**：使用 Optional 标记
- **合并策略**：不同字段有不同的更新方式
- **业务逻辑**：状态间存在依赖关系

### 2. 状态合并策略

LangGraph 使用 `Annotated` 来定义状态合并策略：

```python
from typing import Annotated
import operator

# 列表追加
messages: Annotated[list, add_messages]

# 数值累加
count: Annotated[int, operator.add]

# 字典合并
data: Annotated[dict, operator.or_]

# 自定义合并函数
custom_field: Annotated[list, lambda x, y: x + y if x else y]
```

### 3. 状态更新模式

节点函数只需返回要更新的字段：

```python
def update_user_info(state: ComplexState):
    """只更新用户信息"""
    return {
        "user_name": "张三",
        "user_preferences": {"theme": "dark"}
    }

def increment_counter(state: ComplexState):
    """增加计数器"""
    return {
        "message_count": 1  # 会与现有值相加
    }
```

## 🔍 代码详细解析

### 状态结构设计

```python
from typing import Annotated, Optional
from typing_extensions import TypedDict
import operator

class ComplexState(TypedDict):
    # 消息历史 - 使用 add_messages 策略
    messages: Annotated[list, add_messages]

    # 用户信息 - 直接替换
    user_name: Optional[str]
    user_preferences: dict

    # 统计信息 - 数值累加
    message_count: Annotated[int, operator.add]

    # 上下文信息 - 直接替换
    current_topic: Optional[str]
    conversation_summary: str
```

**设计原则：**
- **消息历史**：使用专门的消息合并策略
- **用户信息**：直接替换，保持最新状态
- **统计信息**：累加计算，跟踪总量
- **上下文信息**：动态更新，反映当前状态

### 状态分析节点

```python
def analyze_input(state: ComplexState):
    """分析用户输入"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    user_content = last_message.content.lower()

    # 检测话题
    topics = {
        "天气": ["天气", "温度", "下雨", "晴天"],
        "技术": ["编程", "代码", "技术", "开发"],
        "生活": ["生活", "日常", "吃饭", "睡觉"],
    }

    detected_topic = None
    for topic, keywords in topics.items():
        if any(keyword in user_content for keyword in keywords):
            detected_topic = topic
            break

    return {
        "current_topic": detected_topic,
        "message_count": 1  # 增加消息计数
    }
```

### 状态协调节点

```python
def generate_response(state: ComplexState):
    """生成回复，考虑所有状态信息"""
    messages = state["messages"]
    current_topic = state.get("current_topic")
    user_name = state.get("user_name", "朋友")
    message_count = state.get("message_count", 0)

    # 构建上下文感知的系统提示
    system_prompt = f"你是一个友好的助手。"

    if user_name != "朋友":
        system_prompt += f" 用户名是：{user_name}。"

    if current_topic:
        system_prompt += f" 当前话题是：{current_topic}。"

    if message_count > 5:
        system_prompt += f" 这是第 {message_count} 条消息，请保持对话连贯。"

    # 添加系统消息
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages

    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}
```

### 状态摘要节点

```python
def update_summary(state: ComplexState):
    """更新对话摘要"""
    messages = state["messages"]
    message_count = state.get("message_count", 0)

    # 每5条消息更新一次摘要
    if message_count > 0 and message_count % 5 == 0:
        recent_messages = messages[-10:]  # 最近10条消息

        summary_prompt = "请简要总结以下对话内容：\n"
        for msg in recent_messages:
            role = "用户" if msg.get("role") == "user" else "助手"
            summary_prompt += f"{role}: {msg.get('content', '')}\n"

        summary_response = llm.invoke([{"role": "user", "content": summary_prompt}])

        return {"conversation_summary": summary_response.content}

    return {}
```

## 🚀 运行演示

### 状态监控演示

```python
def run_state_management_demo():
    """运行状态管理演示"""
    print("状态管理演示启动！")
    print("这个聊天机器人会跟踪对话状态、话题和统计信息。")
    print("输入 'status' 查看状态。")

    # 初始状态
    current_state = {
        "messages": [],
        "user_name": None,
        "user_preferences": {},
        "message_count": 0,
        "current_topic": None,
        "conversation_summary": ""
    }

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        if user_input.lower() == 'status':
            print_state_status(current_state)
            continue

        # 处理用户输入...
```

### 预期输出

```
用户: 我叫张三
助手: 你好张三！很高兴认识你。

用户: status
=== 当前状态 ===
消息数量: 2
当前话题: 无
用户名: 张三
对话摘要:

用户: 今天天气真好
助手: 是的，张三！今天的天气确实很不错。

用户: status
=== 当前状态 ===
消息数量: 4
当前话题: 天气
用户名: 张三
对话摘要:
```

## 🎯 高级状态管理

### 1. 状态验证

```python
def validate_state(state: ComplexState) -> bool:
    """验证状态一致性"""
    try:
        # 检查必需字段
        if "messages" not in state:
            return False

        # 检查消息计数一致性
        actual_count = len([msg for msg in state["messages"] if msg.get("role") == "user"])
        expected_count = state.get("message_count", 0)

        if abs(actual_count - expected_count) > 1:  # 允许1的误差
            print(f"警告：消息计数不一致 {actual_count} vs {expected_count}")

        # 检查用户名格式
        user_name = state.get("user_name")
        if user_name and (len(user_name) > 50 or not user_name.strip()):
            return False

        return True
    except Exception as e:
        print(f"状态验证错误: {e}")
        return False

def validated_node(original_node):
    """状态验证装饰器"""
    def wrapper(state: ComplexState):
        if not validate_state(state):
            print("警告：输入状态无效")

        result = original_node(state)

        # 验证输出状态
        updated_state = {**state, **result}
        if not validate_state(updated_state):
            print("警告：输出状态无效")

        return result

    return wrapper
```

### 2. 状态快照和恢复

```python
import copy
import json

class StateManager:
    """状态管理器"""

    def __init__(self):
        self.snapshots = {}
        self.current_snapshot_id = 0

    def create_snapshot(self, state: ComplexState) -> str:
        """创建状态快照"""
        snapshot_id = f"snapshot_{self.current_snapshot_id}"
        self.current_snapshot_id += 1

        # 深拷贝状态
        self.snapshots[snapshot_id] = copy.deepcopy(state)

        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> ComplexState:
        """恢复状态快照"""
        if snapshot_id not in self.snapshots:
            raise ValueError(f"快照 {snapshot_id} 不存在")

        return copy.deepcopy(self.snapshots[snapshot_id])

    def list_snapshots(self) -> list:
        """列出所有快照"""
        return list(self.snapshots.keys())

# 使用示例
state_manager = StateManager()

def create_checkpoint(state: ComplexState):
    """创建检查点"""
    snapshot_id = state_manager.create_snapshot(state)
    print(f"已创建检查点: {snapshot_id}")
    return {}
```

### 3. 状态差异分析

```python
def compare_states(state1: ComplexState, state2: ComplexState) -> dict:
    """比较两个状态的差异"""
    differences = {}

    all_keys = set(state1.keys()) | set(state2.keys())

    for key in all_keys:
        val1 = state1.get(key)
        val2 = state2.get(key)

        if val1 != val2:
            differences[key] = {
                "before": val1,
                "after": val2,
                "type": "modified" if key in state1 and key in state2 else
                       "added" if key in state2 else "removed"
            }

    return differences

def state_diff_node(state: ComplexState):
    """状态差异分析节点"""
    # 保存当前状态
    before_state = copy.deepcopy(state)

    # 执行某些操作...
    result = {"message_count": 1}

    # 分析差异
    after_state = {**state, **result}
    differences = compare_states(before_state, after_state)

    if differences:
        print("状态变化:")
        for key, diff in differences.items():
            print(f"  {key}: {diff['before']} -> {diff['after']}")

    return result
```

## 🎯 实践练习

### 练习1：用户偏好管理

```python
def update_user_preferences(state: ComplexState):
    """更新用户偏好"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    content = last_message.content.lower()
    preferences = state.get("user_preferences", {})

    # 检测偏好设置
    if "我喜欢" in content:
        likes = preferences.get("likes", [])
        new_like = content.replace("我喜欢", "").strip()
        if new_like and new_like not in likes:
            likes.append(new_like)
            preferences["likes"] = likes

    if "我不喜欢" in content:
        dislikes = preferences.get("dislikes", [])
        new_dislike = content.replace("我不喜欢", "").strip()
        if new_dislike and new_dislike not in dislikes:
            dislikes.append(new_dislike)
            preferences["dislikes"] = dislikes

    if "主题" in content and ("深色" in content or "浅色" in content):
        theme = "dark" if "深色" in content else "light"
        preferences["theme"] = theme

    return {"user_preferences": preferences}
```

### 练习2：对话质量评估

```python
def evaluate_conversation_quality(state: ComplexState):
    """评估对话质量"""
    messages = state["messages"]
    message_count = state.get("message_count", 0)

    if message_count < 3:
        return {}

    # 计算对话质量指标
    user_messages = [msg for msg in messages if msg.get("role") == "user"]
    assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]

    # 平均消息长度
    avg_user_length = sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages)
    avg_assistant_length = sum(len(msg.get("content", "")) for msg in assistant_messages) / len(assistant_messages)

    # 话题一致性
    current_topic = state.get("current_topic")
    topic_consistency = 1.0 if current_topic else 0.5

    # 综合评分
    quality_score = min(1.0, (avg_user_length + avg_assistant_length) / 200 * topic_consistency)

    return {
        "conversation_quality": {
            "score": quality_score,
            "avg_user_length": avg_user_length,
            "avg_assistant_length": avg_assistant_length,
            "topic_consistency": topic_consistency
        }
    }
```

### 练习3：状态持久化

```python
import pickle
import os

class StatePersistence:
    """状态持久化管理"""

    def __init__(self, storage_path: str = "state_storage"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def save_state(self, state: ComplexState, session_id: str):
        """保存状态到文件"""
        file_path = os.path.join(self.storage_path, f"{session_id}.pkl")

        try:
            with open(file_path, 'wb') as f:
                pickle.dump(state, f)
            print(f"状态已保存: {file_path}")
        except Exception as e:
            print(f"保存状态失败: {e}")

    def load_state(self, session_id: str) -> ComplexState:
        """从文件加载状态"""
        file_path = os.path.join(self.storage_path, f"{session_id}.pkl")

        try:
            with open(file_path, 'rb') as f:
                state = pickle.load(f)
            print(f"状态已加载: {file_path}")
            return state
        except FileNotFoundError:
            print(f"状态文件不存在: {file_path}")
            return self.get_default_state()
        except Exception as e:
            print(f"加载状态失败: {e}")
            return self.get_default_state()

    def get_default_state(self) -> ComplexState:
        """获取默认状态"""
        return {
            "messages": [],
            "user_name": None,
            "user_preferences": {},
            "message_count": 0,
            "current_topic": None,
            "conversation_summary": ""
        }

# 使用示例
persistence = StatePersistence()

def save_state_node(state: ComplexState):
    """保存状态节点"""
    session_id = state.get("session_id", "default")
    persistence.save_state(state, session_id)
    return {}
```

## 🔧 常见问题

### Q1: 状态字段太多，如何组织？

**答：** 使用嵌套状态结构：

```python
class UserInfo(TypedDict):
    name: Optional[str]
    preferences: dict
    settings: dict

class ConversationInfo(TypedDict):
    topic: Optional[str]
    summary: str
    quality_score: float

class ComplexState(TypedDict):
    messages: Annotated[list, add_messages]
    user: UserInfo
    conversation: ConversationInfo
    statistics: dict
```

### Q2: 状态更新冲突怎么处理？

**答：** 实现状态锁和版本控制：

```python
import threading
from typing import Any

class VersionedState:
    def __init__(self, initial_state: dict):
        self.state = initial_state
        self.version = 0
        self.lock = threading.Lock()

    def update(self, updates: dict, expected_version: int = None):
        with self.lock:
            if expected_version is not None and self.version != expected_version:
                raise ValueError(f"版本冲突: 期望 {expected_version}, 实际 {self.version}")

            self.state.update(updates)
            self.version += 1

            return self.version
```

### Q3: 如何处理状态的内存占用？

**答：** 实现状态压缩和清理：

```python
def compress_state(state: ComplexState) -> ComplexState:
    """压缩状态，减少内存占用"""
    compressed = copy.deepcopy(state)

    # 限制消息历史长度
    if len(compressed["messages"]) > 50:
        compressed["messages"] = compressed["messages"][-50:]

    # 清理过期的临时数据
    if "temp_data" in compressed:
        del compressed["temp_data"]

    # 压缩摘要
    summary = compressed.get("conversation_summary", "")
    if len(summary) > 1000:
        compressed["conversation_summary"] = summary[:1000] + "..."

    return compressed
```

## 📖 相关资源

### 官方文档
- [LangGraph 状态管理](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [状态合并策略](https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers)

### 下一步学习
- [06. 内存检查点教学](06_memory_checkpoint_tutorial.md) - 状态持久化
- [11. 短期记忆教学](11_short_term_memory_tutorial.md) - 记忆管理

### 代码示例
- 完整代码：[05_state_management.py](../../teach_code/05_state_management.py)
- 运行方式：`python teach_code/05_state_management.py`

## 🌟 总结

复杂状态管理是构建高级 LangGraph 应用的关键：

1. **结构设计**：合理的状态字段组织
2. **合并策略**：不同数据类型的更新方式
3. **一致性保证**：状态验证和错误处理
4. **性能优化**：状态压缩和内存管理
5. **持久化**：状态的保存和恢复机制

掌握状态管理后，你可以构建具有复杂业务逻辑的智能应用！
