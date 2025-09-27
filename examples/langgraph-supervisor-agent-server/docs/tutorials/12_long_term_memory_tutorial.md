# 12. 长期记忆教学

## 🎯 学习目标

通过这个教程，你将学会：
- 长期记忆的概念和持久化机制
- 如何使用 Store 实现跨会话记忆
- 记忆的检索、更新和管理策略
- 构建个性化用户档案系统

## 📚 核心概念

### 1. 什么是长期记忆？

长期记忆是指**跨会话持久化存储**的用户信息和交互历史：

```
会话1 → 存储用户信息 → 会话结束
会话2 → 检索历史信息 → 个性化服务 → 更新记忆
```

**长期记忆的特点：**
- **持久化**：跨会话、跨时间保存
- **累积性**：随时间不断积累和丰富
- **个性化**：为每个用户建立独特档案
- **可检索**：支持高效的信息查询

### 2. Store 存储系统

LangGraph 使用 Store 实现长期记忆：

```python
from langgraph.store.memory import InMemoryStore

# 创建存储
store = InMemoryStore()

# 存储用户信息
store.put(("users",), "user_123", {"name": "张三", "age": 25})

# 检索用户信息
user_info = store.get(("users",), "user_123")
```

### 3. 记忆层次结构

```python
# 用户基本信息
("users",) → user_id → {name, age, location, ...}

# 用户偏好
("preferences",) → user_id → {likes, dislikes, settings, ...}

# 交互历史
("interactions",) → user_id → [{timestamp, type, content}, ...]

# 学习记录
("learning",) → user_id → {topics, progress, achievements, ...}
```

## 🔍 代码详细解析

### 基础长期记忆系统

```python
from langgraph.store.memory import InMemoryStore
import datetime
import json

# 创建存储
store = InMemoryStore()

# 预填充一些用户数据
store.put(("users",), "user_123", {
    "name": "张三",
    "age": 25,
    "location": "北京",
    "joined_date": "2024-01-01"
})

store.put(("preferences",), "user_123", {
    "language": "zh",
    "theme": "dark",
    "interests": ["技术", "编程", "AI"]
})

def load_user_memory(user_id: str, store: InMemoryStore) -> dict:
    """加载用户长期记忆"""
    memory = {
        "user_info": None,
        "preferences": None,
        "interactions": [],
        "learning_progress": None
    }

    # 加载用户基本信息
    user_memory = store.get(("users",), user_id)
    if user_memory:
        memory["user_info"] = user_memory.value

    # 加载用户偏好
    pref_memory = store.get(("preferences",), user_id)
    if pref_memory:
        memory["preferences"] = pref_memory.value

    # 加载交互历史
    interaction_memory = store.get(("interactions",), user_id)
    if interaction_memory:
        memory["interactions"] = interaction_memory.value

    # 加载学习进度
    learning_memory = store.get(("learning",), user_id)
    if learning_memory:
        memory["learning_progress"] = learning_memory.value

    return memory

def save_interaction(user_id: str, interaction_type: str, content: str, store: InMemoryStore):
    """保存交互记录"""
    # 获取现有交互历史
    existing_memory = store.get(("interactions",), user_id)
    interactions = existing_memory.value if existing_memory else []

    # 添加新交互
    new_interaction = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": interaction_type,
        "content": content
    }
    interactions.append(new_interaction)

    # 限制历史长度（保留最近100条）
    if len(interactions) > 100:
        interactions = interactions[-100:]

    # 保存更新后的历史
    store.put(("interactions",), user_id, interactions)
```

### 个性化处理节点

```python
def personalized_greeting(state: State, *, store: InMemoryStore, user_id: str) -> State:
    """个性化问候"""
    # 加载用户记忆
    memory = load_user_memory(user_id, store)

    user_info = memory.get("user_info", {})
    preferences = memory.get("preferences", {})
    interactions = memory.get("interactions", [])

    # 构建个性化问候
    greeting_parts = []

    # 基于用户信息
    if user_info.get("name"):
        name = user_info["name"]
        greeting_parts.append(f"你好，{name}！")

        # 检查是否是老用户
        if interactions:
            last_interaction = interactions[-1]
            last_time = datetime.datetime.fromisoformat(last_interaction["timestamp"])
            days_ago = (datetime.datetime.now() - last_time).days

            if days_ago > 7:
                greeting_parts.append(f"好久不见，上次聊天是{days_ago}天前。")
            elif days_ago > 0:
                greeting_parts.append(f"欢迎回来！")
            else:
                greeting_parts.append("很高兴再次见到你！")
    else:
        greeting_parts.append("你好！很高兴认识你。")

    # 基于用户偏好
    if preferences.get("interests"):
        interests = preferences["interests"]
        greeting_parts.append(f"我记得你对{', '.join(interests)}很感兴趣。")

    greeting = " ".join(greeting_parts)

    # 保存这次交互
    save_interaction(user_id, "greeting", greeting, store)

    return {"messages": [{"role": "assistant", "content": greeting}]}

def update_user_profile(state: State, *, store: InMemoryStore, user_id: str) -> State:
    """更新用户档案"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    content = last_message.content

    # 提取用户信息
    updates = {}

    # 提取姓名
    if "我叫" in content or "我的名字是" in content:
        import re
        name_match = re.search(r"(?:我叫|我的名字是)(.+)", content)
        if name_match:
            name = name_match.group(1).strip()

            # 更新用户信息
            existing_info = store.get(("users",), user_id)
            user_info = existing_info.value if existing_info else {}
            user_info["name"] = name
            user_info["last_updated"] = datetime.datetime.now().isoformat()

            store.put(("users",), user_id, user_info)
            updates["user_name_updated"] = True

    # 提取兴趣爱好
    if "我喜欢" in content or "我对" in content and "感兴趣" in content:
        existing_prefs = store.get(("preferences",), user_id)
        preferences = existing_prefs.value if existing_prefs else {}

        interests = preferences.get("interests", [])

        # 简单的兴趣提取
        if "我喜欢" in content:
            interest = content.split("我喜欢")[1].strip()
            if interest and interest not in interests:
                interests.append(interest)

        preferences["interests"] = interests
        preferences["last_updated"] = datetime.datetime.now().isoformat()

        store.put(("preferences",), user_id, preferences)
        updates["interests_updated"] = True

    # 保存交互记录
    save_interaction(user_id, "profile_update", content, store)

    return updates
```

### 智能记忆检索

```python
def intelligent_memory_retrieval(state: State, *, store: InMemoryStore, user_id: str) -> State:
    """智能记忆检索"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    query = last_message.content.lower()

    # 加载用户记忆
    memory = load_user_memory(user_id, store)

    # 构建上下文感知的回复
    context_parts = []

    # 检索相关的历史交互
    interactions = memory.get("interactions", [])
    relevant_interactions = []

    for interaction in interactions[-20:]:  # 检查最近20次交互
        if any(keyword in interaction["content"].lower() for keyword in query.split()):
            relevant_interactions.append(interaction)

    if relevant_interactions:
        context_parts.append("根据我们之前的对话...")

    # 检索用户偏好
    preferences = memory.get("preferences", {})
    if preferences.get("interests"):
        user_interests = preferences["interests"]
        query_interests = [interest for interest in user_interests if interest.lower() in query]
        if query_interests:
            context_parts.append(f"考虑到你对{', '.join(query_interests)}的兴趣...")

    # 构建系统提示
    if context_parts:
        system_prompt = f"你是一个有记忆的助手。{' '.join(context_parts)} 请基于用户的历史和偏好提供个性化回复。"
    else:
        system_prompt = "你是一个友好的助手。"

    # 生成回复
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
    response = llm.invoke(enhanced_messages)

    # 保存这次交互
    save_interaction(user_id, "query_response", f"Q: {query} A: {response.content}", store)

    return {"messages": [response]}
```

## 🚀 高级长期记忆模式

### 1. 用户档案管理

```python
class UserProfileManager:
    """用户档案管理器"""

    def __init__(self, store: InMemoryStore):
        self.store = store

    def create_user_profile(self, user_id: str, initial_data: dict):
        """创建用户档案"""
        profile = {
            "created_at": datetime.datetime.now().isoformat(),
            "last_active": datetime.datetime.now().isoformat(),
            "interaction_count": 0,
            **initial_data
        }

        self.store.put(("users",), user_id, profile)

        # 初始化其他记忆类型
        self.store.put(("preferences",), user_id, {})
        self.store.put(("interactions",), user_id, [])
        self.store.put(("learning",), user_id, {})

    def get_user_profile(self, user_id: str) -> dict:
        """获取完整用户档案"""
        profile = {
            "basic_info": {},
            "preferences": {},
            "interaction_stats": {},
            "learning_progress": {}
        }

        # 基本信息
        user_memory = self.store.get(("users",), user_id)
        if user_memory:
            profile["basic_info"] = user_memory.value

        # 偏好设置
        pref_memory = self.store.get(("preferences",), user_id)
        if pref_memory:
            profile["preferences"] = pref_memory.value

        # 交互统计
        interaction_memory = self.store.get(("interactions",), user_id)
        if interaction_memory:
            interactions = interaction_memory.value
            profile["interaction_stats"] = {
                "total_interactions": len(interactions),
                "last_interaction": interactions[-1]["timestamp"] if interactions else None,
                "most_common_topics": self._analyze_topics(interactions)
            }

        # 学习进度
        learning_memory = self.store.get(("learning",), user_id)
        if learning_memory:
            profile["learning_progress"] = learning_memory.value

        return profile

    def _analyze_topics(self, interactions: list) -> list:
        """分析常见话题"""
        topic_counts = {}

        for interaction in interactions:
            content = interaction.get("content", "").lower()

            # 简单的话题检测
            topics = ["技术", "编程", "AI", "生活", "工作", "学习"]
            for topic in topics:
                if topic.lower() in content:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # 返回最常见的3个话题
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:3]]

    def update_activity(self, user_id: str):
        """更新用户活跃度"""
        user_memory = self.store.get(("users",), user_id)
        if user_memory:
            user_data = user_memory.value
            user_data["last_active"] = datetime.datetime.now().isoformat()
            user_data["interaction_count"] = user_data.get("interaction_count", 0) + 1

            self.store.put(("users",), user_id, user_data)
```

### 2. 学习进度跟踪

```python
class LearningProgressTracker:
    """学习进度跟踪器"""

    def __init__(self, store: InMemoryStore):
        self.store = store

    def record_learning_activity(self, user_id: str, topic: str, activity_type: str, details: dict):
        """记录学习活动"""
        learning_memory = self.store.get(("learning",), user_id)
        learning_data = learning_memory.value if learning_memory else {}

        # 初始化话题数据
        if topic not in learning_data:
            learning_data[topic] = {
                "start_date": datetime.datetime.now().isoformat(),
                "activities": [],
                "level": "beginner",
                "achievements": []
            }

        # 添加活动记录
        activity = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": activity_type,
            "details": details
        }

        learning_data[topic]["activities"].append(activity)

        # 更新学习水平
        activity_count = len(learning_data[topic]["activities"])
        if activity_count > 10:
            learning_data[topic]["level"] = "intermediate"
        if activity_count > 25:
            learning_data[topic]["level"] = "advanced"

        # 检查成就
        self._check_achievements(learning_data[topic], activity_count)

        self.store.put(("learning",), user_id, learning_data)

    def _check_achievements(self, topic_data: dict, activity_count: int):
        """检查学习成就"""
        achievements = topic_data.get("achievements", [])

        # 定义成就条件
        achievement_milestones = [
            (5, "初学者"),
            (15, "进步者"),
            (30, "专家"),
            (50, "大师")
        ]

        for milestone, title in achievement_milestones:
            if activity_count >= milestone and title not in achievements:
                achievements.append({
                    "title": title,
                    "earned_at": datetime.datetime.now().isoformat(),
                    "activity_count": activity_count
                })

        topic_data["achievements"] = achievements

    def get_learning_recommendations(self, user_id: str) -> list:
        """获取学习建议"""
        learning_memory = self.store.get(("learning",), user_id)
        if not learning_memory:
            return ["开始你的学习之旅！尝试问一些问题。"]

        learning_data = learning_memory.value
        recommendations = []

        for topic, data in learning_data.items():
            level = data.get("level", "beginner")
            activity_count = len(data.get("activities", []))

            if level == "beginner" and activity_count < 10:
                recommendations.append(f"继续学习{topic}基础知识")
            elif level == "intermediate":
                recommendations.append(f"尝试{topic}的高级概念")
            elif level == "advanced":
                recommendations.append(f"考虑在{topic}领域进行实践项目")

        return recommendations if recommendations else ["探索新的学习领域！"]
```

### 3. 记忆分析和洞察

```python
class MemoryAnalyzer:
    """记忆分析器"""

    def __init__(self, store: InMemoryStore):
        self.store = store

    def analyze_user_patterns(self, user_id: str) -> dict:
        """分析用户模式"""
        analysis = {
            "activity_patterns": {},
            "interest_evolution": {},
            "engagement_trends": {},
            "learning_velocity": {}
        }

        # 分析活动模式
        interaction_memory = self.store.get(("interactions",), user_id)
        if interaction_memory:
            interactions = interaction_memory.value
            analysis["activity_patterns"] = self._analyze_activity_patterns(interactions)

        # 分析兴趣演变
        analysis["interest_evolution"] = self._analyze_interest_evolution(user_id)

        # 分析参与度趋势
        analysis["engagement_trends"] = self._analyze_engagement_trends(user_id)

        return analysis

    def _analyze_activity_patterns(self, interactions: list) -> dict:
        """分析活动模式"""
        if not interactions:
            return {}

        # 按小时统计活动
        hour_counts = {}
        for interaction in interactions:
            timestamp = datetime.datetime.fromisoformat(interaction["timestamp"])
            hour = timestamp.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # 找出最活跃的时间段
        most_active_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 12

        return {
            "most_active_hour": most_active_hour,
            "total_interactions": len(interactions),
            "average_daily_interactions": len(interactions) / max(1, self._get_active_days(interactions))
        }

    def _get_active_days(self, interactions: list) -> int:
        """计算活跃天数"""
        if not interactions:
            return 1

        dates = set()
        for interaction in interactions:
            timestamp = datetime.datetime.fromisoformat(interaction["timestamp"])
            dates.add(timestamp.date())

        return len(dates)

    def _analyze_interest_evolution(self, user_id: str) -> dict:
        """分析兴趣演变"""
        pref_memory = self.store.get(("preferences",), user_id)
        if not pref_memory:
            return {}

        preferences = pref_memory.value
        interests = preferences.get("interests", [])

        return {
            "current_interests": interests,
            "interest_count": len(interests),
            "diversity_score": len(set(interests)) / max(1, len(interests))
        }

    def _analyze_engagement_trends(self, user_id: str) -> dict:
        """分析参与度趋势"""
        learning_memory = self.store.get(("learning",), user_id)
        if not learning_memory:
            return {"trend": "new_user"}

        learning_data = learning_memory.value
        total_activities = sum(len(topic_data.get("activities", [])) for topic_data in learning_data.values())

        if total_activities > 50:
            return {"trend": "highly_engaged"}
        elif total_activities > 20:
            return {"trend": "moderately_engaged"}
        elif total_activities > 5:
            return {"trend": "getting_started"}
        else:
            return {"trend": "new_learner"}

    def generate_insights(self, user_id: str) -> list:
        """生成用户洞察"""
        analysis = self.analyze_user_patterns(user_id)
        insights = []

        # 活动模式洞察
        activity = analysis.get("activity_patterns", {})
        if activity.get("most_active_hour"):
            hour = activity["most_active_hour"]
            if 9 <= hour <= 17:
                insights.append("你倾向于在工作时间学习")
            elif 18 <= hour <= 22:
                insights.append("你是一个晚间学习者")
            else:
                insights.append("你有独特的学习时间偏好")

        # 参与度洞察
        engagement = analysis.get("engagement_trends", {})
        trend = engagement.get("trend", "new_user")

        if trend == "highly_engaged":
            insights.append("你是一个非常活跃的学习者！")
        elif trend == "moderately_engaged":
            insights.append("你保持着良好的学习节奏")
        elif trend == "getting_started":
            insights.append("你正在建立学习习惯")

        # 兴趣洞察
        interests = analysis.get("interest_evolution", {})
        if interests.get("interest_count", 0) > 3:
            insights.append("你有广泛的兴趣爱好")

        return insights if insights else ["继续探索，建立你的学习档案！"]
```

## 🎯 实践练习

### 练习1：个性化推荐系统

```python
class PersonalizationEngine:
    """个性化推荐引擎"""

    def __init__(self, store: InMemoryStore):
        self.store = store
        self.analyzer = MemoryAnalyzer(store)

    def get_personalized_content(self, user_id: str, content_type: str) -> list:
        """获取个性化内容"""
        # 加载用户档案
        profile_manager = UserProfileManager(self.store)
        profile = profile_manager.get_user_profile(user_id)

        # 基于用户兴趣推荐
        interests = profile.get("preferences", {}).get("interests", [])
        learning_progress = profile.get("learning_progress", {})

        recommendations = []

        if content_type == "topics":
            # 推荐学习话题
            if "技术" in interests:
                recommendations.extend(["Python进阶", "机器学习基础", "Web开发"])
            if "AI" in interests:
                recommendations.extend(["深度学习", "自然语言处理", "计算机视觉"])

            # 基于学习进度推荐
            for topic, data in learning_progress.items():
                level = data.get("level", "beginner")
                if level == "beginner":
                    recommendations.append(f"{topic}基础练习")
                elif level == "intermediate":
                    recommendations.append(f"{topic}实战项目")

        elif content_type == "activities":
            # 推荐学习活动
            engagement = self.analyzer.analyze_user_patterns(user_id).get("engagement_trends", {})
            trend = engagement.get("trend", "new_user")

            if trend == "highly_engaged":
                recommendations.extend(["挑战性项目", "高级教程", "专家讨论"])
            elif trend == "moderately_engaged":
                recommendations.extend(["实践练习", "案例研究", "技能测试"])
            else:
                recommendations.extend(["入门教程", "基础概念", "简单练习"])

        return recommendations[:5]  # 返回前5个推荐

    def update_recommendation_feedback(self, user_id: str, recommendation: str, feedback: str):
        """更新推荐反馈"""
        # 存储推荐反馈
        feedback_data = {
            "recommendation": recommendation,
            "feedback": feedback,
            "timestamp": datetime.datetime.now().isoformat()
        }

        existing_feedback = self.store.get(("feedback",), user_id)
        feedback_list = existing_feedback.value if existing_feedback else []
        feedback_list.append(feedback_data)

        self.store.put(("feedback",), user_id, feedback_list)
```

### 练习2：记忆同步和备份

```python
class MemorySyncManager:
    """记忆同步管理器"""

    def __init__(self, store: InMemoryStore):
        self.store = store

    def export_user_memory(self, user_id: str) -> dict:
        """导出用户记忆"""
        export_data = {
            "user_id": user_id,
            "export_timestamp": datetime.datetime.now().isoformat(),
            "data": {}
        }

        # 导出所有记忆类型
        memory_types = ["users", "preferences", "interactions", "learning", "feedback"]

        for memory_type in memory_types:
            memory = self.store.get((memory_type,), user_id)
            if memory:
                export_data["data"][memory_type] = memory.value

        return export_data

    def import_user_memory(self, export_data: dict):
        """导入用户记忆"""
        user_id = export_data["user_id"]
        data = export_data["data"]

        # 导入所有记忆类型
        for memory_type, memory_value in data.items():
            self.store.put((memory_type,), user_id, memory_value)

        print(f"用户 {user_id} 的记忆已导入")

    def backup_all_memories(self) -> dict:
        """备份所有记忆"""
        # 注意：InMemoryStore 不直接支持遍历所有数据
        # 这里提供概念性实现
        backup_data = {
            "backup_timestamp": datetime.datetime.now().isoformat(),
            "users": {}
        }

        # 实际实现需要根据具体的存储后端来遍历数据
        print("记忆备份功能需要根据具体存储实现")

        return backup_data
```

## 🔧 常见问题

### Q1: 长期记忆会无限增长吗？

**答：** 需要实现记忆管理策略：

```python
def cleanup_old_memories(store: InMemoryStore, user_id: str, days_to_keep: int = 90):
    """清理旧记忆"""
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)

    # 清理旧交互记录
    interaction_memory = store.get(("interactions",), user_id)
    if interaction_memory:
        interactions = interaction_memory.value
        recent_interactions = [
            interaction for interaction in interactions
            if datetime.datetime.fromisoformat(interaction["timestamp"]) > cutoff_date
        ]
        store.put(("interactions",), user_id, recent_interactions)
```

### Q2: 如何处理用户隐私？

**答：** 实现隐私保护机制：

```python
def anonymize_user_data(store: InMemoryStore, user_id: str):
    """匿名化用户数据"""
    # 移除敏感信息
    user_memory = store.get(("users",), user_id)
    if user_memory:
        user_data = user_memory.value
        # 移除姓名等敏感信息
        user_data.pop("name", None)
        user_data.pop("location", None)
        store.put(("users",), user_id, user_data)
```

### Q3: 如何迁移到生产环境？

**答：** 使用持久化存储：

```python
# 生产环境使用 Redis 或数据库
from langgraph.store.redis import RedisStore

# Redis 存储
store = RedisStore(redis_url="redis://localhost:6379")

# 或使用数据库存储
# store = DatabaseStore(connection_string="postgresql://...")
```

## 📖 相关资源

### 官方文档
- [LangGraph Store](https://langchain-ai.github.io/langgraph/concepts/persistence/#store)
- [长期记忆模式](https://langchain-ai.github.io/langgraph/concepts/memory/)

### 下一步学习
- [11. 短期记忆教学](11_short_term_memory_tutorial.md) - 记忆对比
- [10. 运行时上下文教学](10_runtime_context_tutorial.md) - 上下文管理

### 代码示例
- 完整代码：[12_long_term_memory.py](../../teach_code/12_long_term_memory.py)
- 运行方式：`python teach_code/12_long_term_memory.py`

## 🌟 总结

长期记忆是构建智能个性化系统的核心：

1. **持久化存储**：跨会话保存用户信息
2. **个性化服务**：基于历史提供定制化体验
3. **学习跟踪**：记录用户成长和进步
4. **智能分析**：从记忆中提取有价值的洞察
5. **隐私保护**：安全地管理用户敏感信息

掌握长期记忆后，你可以构建真正智能的个性化应用！
