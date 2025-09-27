# 11. 短期记忆教学

## 🎯 学习目标

通过这个教程，你将学会：
- 短期记忆的概念和实现原理
- 如何在对话中维护上下文信息
- 记忆的提取、存储和管理
- 不同类型记忆的设计模式

## 📚 核心概念

### 1. 什么是短期记忆？

短期记忆是指在**单次对话会话中**维护和使用的临时信息：

```
对话开始 → 收集信息 → 存储到短期记忆 → 在后续回复中使用 → 对话结束时清除
```

**短期记忆的特点：**
- **会话级别**：只在当前对话中有效
- **动态更新**：随对话进展不断更新
- **上下文相关**：与当前话题和用户意图相关
- **临时性**：对话结束后通常被清除

### 2. 记忆类型

```python
class ComplexState(TypedDict):
    # 消息历史
    messages: Annotated[list, add_messages]

    # 用户信息记忆
    user_name: Optional[str]
    user_preferences: dict

    # 对话统计
    message_count: Annotated[int, operator.add]

    # 上下文记忆
    current_topic: Optional[str]
    conversation_summary: str
```

### 3. 记忆管理策略

- **信息提取**：从用户输入中提取关键信息
- **记忆存储**：将信息存储到状态中
- **记忆检索**：在生成回复时使用记忆
- **记忆更新**：根据新信息更新现有记忆

## 🔍 代码详细解析

### 基础记忆系统

```python
from typing import Annotated, Optional
from typing_extensions import TypedDict
import operator

class ComplexState(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: Optional[str]
    user_preferences: dict
    message_count: Annotated[int, operator.add]
    current_topic: Optional[str]
    conversation_summary: str

def analyze_input(state: ComplexState):
    """分析用户输入并提取记忆信息"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    user_content = last_message.content.lower()
    updates = {}

    # 提取用户名
    if "我叫" in user_content or "名字是" in user_content:
        import re
        name_match = re.search(r"(?:我叫|名字是)(.+)", user_content)
        if name_match:
            name = name_match.group(1).strip()
            updates["user_name"] = name

    # 提取偏好信息
    preferences = state.get("user_preferences", {})
    if "我喜欢" in user_content:
        likes = preferences.get("likes", [])
        preference = user_content.replace("我喜欢", "").strip()
        if preference and preference not in likes:
            likes.append(preference)
            preferences["likes"] = likes
            updates["user_preferences"] = preferences

    # 检测话题变化
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

    if detected_topic:
        updates["current_topic"] = detected_topic

    # 增加消息计数
    updates["message_count"] = 1

    return updates
```

### 记忆增强的回复生成

```python
def generate_response(state: ComplexState):
    """生成记忆增强的回复"""
    messages = state["messages"]
    current_topic = state.get("current_topic")
    user_name = state.get("user_name", "朋友")
    message_count = state.get("message_count", 0)
    user_preferences = state.get("user_preferences", {})

    # 构建上下文感知的系统提示
    system_prompt = f"你是一个友好的助手。"

    if user_name != "朋友":
        system_prompt += f" 用户名是：{user_name}。"

    if current_topic:
        system_prompt += f" 当前话题是：{current_topic}。"

    if message_count > 5:
        system_prompt += f" 这是第 {message_count} 条消息，请保持对话连贯。"

    # 添加用户偏好信息
    if user_preferences.get("likes"):
        likes = ", ".join(user_preferences["likes"])
        system_prompt += f" 用户喜欢：{likes}。"

    # 生成回复
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}

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

### 图构建和演示

```python
# 构建图
graph_builder = StateGraph(ComplexState)
graph_builder.add_node("analyze", analyze_input)
graph_builder.add_node("respond", generate_response)
graph_builder.add_node("summarize", update_summary)

graph_builder.add_edge(START, "analyze")
graph_builder.add_edge("analyze", "respond")
graph_builder.add_edge("respond", "summarize")
graph_builder.add_edge("summarize", END)

# 编译图
memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

def run_short_term_memory_demo():
    """运行短期记忆演示"""
    print("短期记忆演示启动！")
    print("这个智能体会记住对话中的信息并在后续回复中使用。")

    config = {"configurable": {"thread_id": "memory_demo"}}

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        if user_input.lower() == 'status':
            # 显示当前记忆状态
            current_state = graph.get_state(config)
            if current_state.values:
                print_memory_status(current_state.values)
            continue

        try:
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config
            )

            assistant_message = result["messages"][-1]
            print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")

def print_memory_status(state: dict):
    """打印记忆状态"""
    print("\n=== 当前记忆状态 ===")
    print(f"用户名: {state.get('user_name', '未知')}")
    print(f"消息数量: {state.get('message_count', 0)}")
    print(f"当前话题: {state.get('current_topic', '无')}")

    preferences = state.get('user_preferences', {})
    if preferences.get('likes'):
        print(f"用户偏好: {', '.join(preferences['likes'])}")

    summary = state.get('conversation_summary', '')
    if summary:
        print(f"对话摘要: {summary}")
```

## 🚀 高级记忆模式

### 1. 分层记忆系统

```python
class LayeredMemoryState(TypedDict):
    messages: Annotated[list, add_messages]

    # 个人信息层
    personal_info: dict

    # 偏好层
    preferences: dict

    # 事实层
    facts: dict

    # 情节层
    episodic: list

def layered_memory_processor(state: LayeredMemoryState):
    """分层记忆处理器"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    content = last_message.content
    updates = {}

    # 个人信息层
    personal_info = state.get("personal_info", {})
    if "我叫" in content:
        import re
        name_match = re.search(r"我叫(.+)", content)
        if name_match:
            personal_info["name"] = name_match.group(1).strip()
            updates["personal_info"] = personal_info

    # 偏好层
    preferences = state.get("preferences", {})
    if "我喜欢" in content:
        likes = preferences.get("likes", [])
        preference = content.replace("我喜欢", "").strip()
        if preference not in likes:
            likes.append(preference)
            preferences["likes"] = likes
            updates["preferences"] = preferences

    # 事实层
    facts = state.get("facts", {})
    if "今天" in content and ("天气" in content or "温度" in content):
        facts["today_weather"] = content
        updates["facts"] = facts

    # 情节层
    episodic = state.get("episodic", [])
    episodic.append({
        "timestamp": len(episodic) + 1,
        "content": content,
        "type": "user_input"
    })
    updates["episodic"] = episodic

    return updates
```

### 2. 智能记忆检索

```python
class SmartMemoryRetriever:
    """智能记忆检索器"""

    def __init__(self):
        self.memory_weights = {
            "personal_info": 1.0,
            "preferences": 0.8,
            "current_topic": 0.9,
            "recent_facts": 0.7
        }

    def retrieve_relevant_memory(self, state: dict, query: str) -> dict:
        """检索相关记忆"""
        relevant_memory = {}

        # 检索个人信息
        personal_info = state.get("personal_info", {})
        if personal_info and any(keyword in query.lower() for keyword in ["名字", "我", "你"]):
            relevant_memory["personal_info"] = personal_info

        # 检索偏好信息
        preferences = state.get("preferences", {})
        if preferences and "喜欢" in query.lower():
            relevant_memory["preferences"] = preferences

        # 检索话题相关信息
        current_topic = state.get("current_topic")
        if current_topic and current_topic.lower() in query.lower():
            relevant_memory["current_topic"] = current_topic

        return relevant_memory

    def generate_memory_prompt(self, relevant_memory: dict) -> str:
        """生成记忆提示"""
        prompt_parts = []

        if relevant_memory.get("personal_info"):
            info = relevant_memory["personal_info"]
            if info.get("name"):
                prompt_parts.append(f"用户名是{info['name']}")

        if relevant_memory.get("preferences"):
            prefs = relevant_memory["preferences"]
            if prefs.get("likes"):
                likes = ", ".join(prefs["likes"])
                prompt_parts.append(f"用户喜欢{likes}")

        if relevant_memory.get("current_topic"):
            topic = relevant_memory["current_topic"]
            prompt_parts.append(f"当前讨论{topic}")

        return "。".join(prompt_parts) + "。" if prompt_parts else ""

def smart_memory_response(state: ComplexState):
    """智能记忆回复"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    # 检索相关记忆
    retriever = SmartMemoryRetriever()
    relevant_memory = retriever.retrieve_relevant_memory(state, last_message.content)

    # 生成记忆增强的提示
    memory_prompt = retriever.generate_memory_prompt(relevant_memory)

    # 构建系统提示
    system_prompt = "你是一个有记忆的助手。"
    if memory_prompt:
        system_prompt += f" 记住：{memory_prompt}"

    # 生成回复
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}
```

### 3. 记忆压缩和清理

```python
class MemoryManager:
    """记忆管理器"""

    def __init__(self, max_episodic_items: int = 20):
        self.max_episodic_items = max_episodic_items

    def compress_memory(self, state: dict) -> dict:
        """压缩记忆"""
        compressed_state = state.copy()

        # 压缩情节记忆
        episodic = state.get("episodic", [])
        if len(episodic) > self.max_episodic_items:
            # 保留最近的记忆
            compressed_state["episodic"] = episodic[-self.max_episodic_items:]

        # 合并重复的偏好
        preferences = state.get("preferences", {})
        if preferences.get("likes"):
            # 去重
            unique_likes = list(set(preferences["likes"]))
            preferences["likes"] = unique_likes
            compressed_state["preferences"] = preferences

        return compressed_state

    def prioritize_memory(self, state: dict, importance_threshold: float = 0.5) -> dict:
        """记忆优先级排序"""
        # 简化实现：根据使用频率确定重要性
        prioritized_state = state.copy()

        # 统计偏好使用频率
        preferences = state.get("preferences", {})
        if preferences.get("likes"):
            # 这里可以实现更复杂的重要性评分
            # 简化为保持原样
            pass

        return prioritized_state

    def cleanup_stale_memory(self, state: dict, max_age_minutes: int = 60) -> dict:
        """清理过期记忆"""
        cleaned_state = state.copy()

        # 清理过期的事实
        facts = state.get("facts", {})
        current_time = datetime.datetime.now()

        # 简化实现：清理今日天气信息（如果是昨天的）
        if "today_weather" in facts:
            # 实际应用中需要检查时间戳
            pass

        return cleaned_state

def memory_maintenance(state: ComplexState):
    """记忆维护"""
    manager = MemoryManager()

    # 压缩记忆
    compressed_state = manager.compress_memory(state)

    # 优先级排序
    prioritized_state = manager.prioritize_memory(compressed_state)

    # 清理过期记忆
    cleaned_state = manager.cleanup_stale_memory(prioritized_state)

    return cleaned_state
```

## 🎯 实践练习

### 练习1：情感记忆系统

```python
class EmotionalMemoryState(TypedDict):
    messages: Annotated[list, add_messages]
    emotional_state: dict
    mood_history: list
    empathy_level: float

def emotional_memory_processor(state: EmotionalMemoryState):
    """情感记忆处理器"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    content = last_message.content.lower()

    # 情感分析
    positive_words = ["开心", "高兴", "快乐", "满意", "好"]
    negative_words = ["难过", "生气", "失望", "沮丧", "坏"]

    emotion_score = 0
    for word in positive_words:
        if word in content:
            emotion_score += 1

    for word in negative_words:
        if word in content:
            emotion_score -= 1

    # 更新情感状态
    emotional_state = state.get("emotional_state", {"valence": 0, "arousal": 0})
    emotional_state["valence"] = emotion_score

    # 更新情绪历史
    mood_history = state.get("mood_history", [])
    mood_history.append({
        "timestamp": len(mood_history) + 1,
        "valence": emotion_score,
        "content": content[:50]  # 截取前50个字符
    })

    # 限制历史长度
    if len(mood_history) > 10:
        mood_history = mood_history[-10:]

    # 计算共情水平
    recent_emotions = [item["valence"] for item in mood_history[-5:]]
    empathy_level = sum(recent_emotions) / len(recent_emotions) if recent_emotions else 0

    return {
        "emotional_state": emotional_state,
        "mood_history": mood_history,
        "empathy_level": empathy_level
    }

def empathetic_response(state: EmotionalMemoryState):
    """共情回复"""
    emotional_state = state.get("emotional_state", {})
    empathy_level = state.get("empathy_level", 0)

    # 根据情感状态调整回复风格
    if empathy_level > 0.5:
        system_prompt = "你是一个温暖、积极的助手。用户情绪较好，请保持轻松愉快的对话风格。"
    elif empathy_level < -0.5:
        system_prompt = "你是一个体贴、理解的助手。用户情绪较低，请给予关怀和支持。"
    else:
        system_prompt = "你是一个友好的助手。保持中性、专业的对话风格。"

    messages = state["messages"]
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}
```

### 练习2：学习记忆系统

```python
class LearningMemoryState(TypedDict):
    messages: Annotated[list, add_messages]
    knowledge_base: dict
    learning_progress: dict
    user_questions: list

def learning_memory_processor(state: LearningMemoryState):
    """学习记忆处理器"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    content = last_message.content
    updates = {}

    # 检测学习内容
    if "什么是" in content or "如何" in content or "为什么" in content:
        # 记录用户问题
        user_questions = state.get("user_questions", [])
        user_questions.append({
            "question": content,
            "timestamp": len(user_questions) + 1
        })
        updates["user_questions"] = user_questions

        # 更新学习进度
        learning_progress = state.get("learning_progress", {})
        topic = extract_topic_from_question(content)
        if topic:
            progress = learning_progress.get(topic, {"questions": 0, "level": "beginner"})
            progress["questions"] += 1

            # 根据问题数量调整水平
            if progress["questions"] > 5:
                progress["level"] = "intermediate"
            if progress["questions"] > 10:
                progress["level"] = "advanced"

            learning_progress[topic] = progress
            updates["learning_progress"] = learning_progress

    # 检测知识分享
    if "我知道" in content or "我学过" in content:
        knowledge_base = state.get("knowledge_base", {})
        # 简化实现：存储用户分享的知识
        knowledge_base[f"user_knowledge_{len(knowledge_base)}"] = content
        updates["knowledge_base"] = knowledge_base

    return updates

def extract_topic_from_question(question: str) -> str:
    """从问题中提取主题"""
    topics = {
        "编程": ["编程", "代码", "程序", "开发"],
        "数学": ["数学", "计算", "公式", "算法"],
        "科学": ["科学", "物理", "化学", "生物"]
    }

    question_lower = question.lower()
    for topic, keywords in topics.items():
        if any(keyword in question_lower for keyword in keywords):
            return topic

    return "通用"

def adaptive_teaching_response(state: LearningMemoryState):
    """自适应教学回复"""
    learning_progress = state.get("learning_progress", {})
    user_questions = state.get("user_questions", [])

    # 分析用户学习水平
    if user_questions:
        last_question = user_questions[-1]["question"]
        topic = extract_topic_from_question(last_question)

        progress = learning_progress.get(topic, {"level": "beginner"})
        level = progress["level"]

        # 根据水平调整回复风格
        if level == "beginner":
            system_prompt = "用简单易懂的语言解释，提供基础概念和例子。"
        elif level == "intermediate":
            system_prompt = "提供更深入的解释，包含一些技术细节。"
        else:
            system_prompt = "提供高级内容，包含复杂概念和深度分析。"

        system_prompt = f"你是一个{topic}领域的教师。{system_prompt}"
    else:
        system_prompt = "你是一个友好的助手。"

    messages = state["messages"]
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}
```

### 练习3：上下文记忆系统

```python
class ContextualMemoryState(TypedDict):
    messages: Annotated[list, add_messages]
    context_stack: list
    reference_memory: dict
    conversation_flow: list

def contextual_memory_processor(state: ContextualMemoryState):
    """上下文记忆处理器"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    content = last_message.content
    updates = {}

    # 管理上下文栈
    context_stack = state.get("context_stack", [])

    # 检测上下文切换
    context_switches = ["回到", "继续", "之前", "刚才"]
    if any(switch in content for switch in context_switches):
        # 尝试恢复之前的上下文
        if len(context_stack) > 1:
            current_context = context_stack.pop()
            updates["context_stack"] = context_stack

    # 检测新话题
    if "我们来谈谈" in content or "换个话题" in content:
        # 推入新上下文
        new_context = {
            "topic": extract_topic_from_content(content),
            "start_message": len(messages),
            "timestamp": len(context_stack)
        }
        context_stack.append(new_context)
        updates["context_stack"] = context_stack

    # 更新引用记忆
    reference_memory = state.get("reference_memory", {})
    if "这个" in content or "那个" in content or "它" in content:
        # 记录可能的引用
        if context_stack:
            current_context = context_stack[-1]
            topic = current_context.get("topic", "unknown")
            reference_memory[f"ref_{len(reference_memory)}"] = {
                "content": content,
                "context": topic,
                "message_index": len(messages)
            }
            updates["reference_memory"] = reference_memory

    # 更新对话流
    conversation_flow = state.get("conversation_flow", [])
    conversation_flow.append({
        "message_index": len(messages),
        "content_summary": content[:30],
        "context": context_stack[-1] if context_stack else None
    })
    updates["conversation_flow"] = conversation_flow

    return updates

def extract_topic_from_content(content: str) -> str:
    """从内容中提取话题"""
    # 简化实现
    if "技术" in content or "编程" in content:
        return "技术"
    elif "生活" in content or "日常" in content:
        return "生活"
    elif "工作" in content or "职业" in content:
        return "工作"
    else:
        return "通用"

def contextual_response(state: ContextualMemoryState):
    """上下文感知回复"""
    context_stack = state.get("context_stack", [])
    reference_memory = state.get("reference_memory", {})

    # 构建上下文提示
    context_prompt = "你是一个有上下文记忆的助手。"

    if context_stack:
        current_context = context_stack[-1]
        topic = current_context.get("topic", "通用")
        context_prompt += f" 当前讨论的主题是{topic}。"

        if len(context_stack) > 1:
            previous_topics = [ctx.get("topic", "未知") for ctx in context_stack[:-1]]
            context_prompt += f" 之前讨论过：{', '.join(previous_topics)}。"

    if reference_memory:
        context_prompt += " 注意用户可能会引用之前提到的内容。"

    messages = state["messages"]
    enhanced_messages = [{"role": "system", "content": context_prompt}] + messages
    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}
```

## 🔧 常见问题

### Q1: 短期记忆会占用多少内存？

**答：** 取决于记忆的复杂度和对话长度：

```python
def estimate_memory_usage(state: dict) -> dict:
    """估算记忆使用量"""
    import sys

    usage = {}
    for key, value in state.items():
        if key != "messages":  # 排除消息历史
            size = sys.getsizeof(value)
            usage[key] = f"{size} bytes"

    return usage
```

### Q2: 如何处理记忆冲突？

**答：** 实现记忆优先级和冲突解决：

```python
def resolve_memory_conflict(old_info: dict, new_info: dict) -> dict:
    """解决记忆冲突"""
    resolved = old_info.copy()

    for key, new_value in new_info.items():
        if key in resolved:
            old_value = resolved[key]

            # 时间戳优先
            if isinstance(new_value, dict) and "timestamp" in new_value:
                if new_value["timestamp"] > old_value.get("timestamp", 0):
                    resolved[key] = new_value
            else:
                # 简单覆盖
                resolved[key] = new_value
        else:
            resolved[key] = new_value

    return resolved
```

### Q3: 短期记忆如何转换为长期记忆？

**答：** 实现记忆转换机制：

```python
def convert_to_long_term(short_term_state: dict, importance_threshold: float = 0.8) -> dict:
    """转换为长期记忆"""
    long_term_memory = {}

    # 评估重要性
    for key, value in short_term_state.items():
        importance = calculate_importance(key, value)

        if importance >= importance_threshold:
            long_term_memory[key] = {
                "value": value,
                "importance": importance,
                "created_at": datetime.datetime.now().isoformat()
            }

    return long_term_memory

def calculate_importance(key: str, value) -> float:
    """计算记忆重要性"""
    # 简化实现
    importance_weights = {
        "user_name": 1.0,
        "user_preferences": 0.9,
        "current_topic": 0.6,
        "message_count": 0.3
    }

    return importance_weights.get(key, 0.5)
```

## 📖 相关资源

### 官方文档
- [LangGraph 状态管理](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [记忆模式](https://langchain-ai.github.io/langgraph/concepts/memory/)

### 下一步学习
- [12. 长期记忆教学](12_long_term_memory_tutorial.md) - 持久化记忆
- [05. 状态管理教学](05_state_management_tutorial.md) - 状态设计

### 代码示例
- 完整代码：[11_short_term_memory.py](../../teach_code/11_short_term_memory.py)
- 运行方式：`python teach_code/11_short_term_memory.py`

## 🌟 总结

短期记忆是构建智能对话系统的关键：

1. **上下文维护**：在对话中保持信息连贯性
2. **个性化交互**：根据用户信息提供定制服务
3. **智能检索**：根据需要检索相关记忆
4. **动态管理**：压缩、清理和优化记忆使用
5. **情感理解**：记住用户情感状态和偏好

掌握短期记忆后，你可以构建更智能、更人性化的对话应用！
