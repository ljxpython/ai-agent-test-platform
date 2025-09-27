# 14. 子图内存教学

## 🎯 学习目标

通过这个教程，你将学会：
- 子图独立内存的概念和优势
- 如何为子图配置独立的检查点
- 子图间的内存隔离和共享策略
- 复杂应用的内存架构设计

## 📚 核心概念

### 1. 什么是子图独立内存？

子图独立内存是指每个子图拥有**自己的检查点和状态管理**：

```
主图内存 ← 独立管理
├── 子图A内存 ← 独立检查点
├── 子图B内存 ← 独立检查点
└── 子图C内存 ← 独立检查点
```

**独立内存的优势：**
- **隔离性**：子图故障不影响其他子图
- **可扩展性**：每个子图可独立扩展
- **可维护性**：独立的状态管理和调试
- **性能优化**：针对性的内存优化策略

### 2. 内存配置

```python
from langgraph.checkpoint.memory import InMemorySaver

# 为每个子图创建独立的检查点
subgraph_a_memory = InMemorySaver()
subgraph_b_memory = InMemorySaver()

# 编译时指定检查点
subgraph_a = builder_a.compile(checkpointer=subgraph_a_memory)
subgraph_b = builder_b.compile(checkpointer=subgraph_b_memory)
```

### 3. 内存层次结构

```
应用级内存
├── 主图内存（全局状态）
├── 子图内存（局部状态）
│   ├── 会话级内存
│   ├── 任务级内存
│   └── 临时内存
└── 共享内存（跨子图数据）
```

## 🔍 代码详细解析

### 基础子图内存设置

```python
from langgraph.checkpoint.memory import InMemorySaver
from typing_extensions import TypedDict

# 定义子图状态
class UserProfileState(TypedDict):
    user_id: str
    profile_data: dict
    last_updated: str

class ConversationState(TypedDict):
    user_id: str
    messages: list
    context: dict

# 创建独立的内存保存器
profile_memory = InMemorySaver()
conversation_memory = InMemorySaver()

def update_profile(state: UserProfileState):
    """更新用户档案"""
    user_id = state["user_id"]

    # 模拟档案更新
    profile_data = {
        "name": "张三",
        "preferences": {"language": "zh", "theme": "dark"},
        "last_login": "2024-01-15"
    }

    return {
        "profile_data": profile_data,
        "last_updated": "2024-01-15 10:30:00"
    }

def manage_conversation(state: ConversationState):
    """管理对话"""
    user_id = state["user_id"]
    messages = state.get("messages", [])

    # 添加系统消息
    new_message = {
        "role": "system",
        "content": f"用户 {user_id} 的对话管理已激活"
    }

    messages.append(new_message)

    return {
        "messages": messages,
        "context": {"session_active": True}
    }

# 创建子图
def create_profile_subgraph():
    """创建用户档案子图"""
    builder = StateGraph(UserProfileState)
    builder.add_node("update", update_profile)
    builder.add_edge(START, "update")
    builder.add_edge("update", END)

    # 使用独立内存编译
    return builder.compile(checkpointer=profile_memory)

def create_conversation_subgraph():
    """创建对话子图"""
    builder = StateGraph(ConversationState)
    builder.add_node("manage", manage_conversation)
    builder.add_edge(START, "manage")
    builder.add_edge("manage", END)

    # 使用独立内存编译
    return builder.compile(checkpointer=conversation_memory)

# 创建子图实例
profile_subgraph = create_profile_subgraph()
conversation_subgraph = create_conversation_subgraph()
```

### 主图协调子图内存

```python
class MainState(TypedDict):
    user_id: str
    operation: str
    profile_result: dict
    conversation_result: dict
    final_status: str

def coordinate_subgraphs(state: MainState):
    """协调子图执行"""
    user_id = state["user_id"]
    operation = state["operation"]

    results = {}

    # 根据操作类型调用不同子图
    if operation in ["profile", "both"]:
        # 调用档案子图
        profile_config = {"configurable": {"thread_id": f"profile_{user_id}"}}
        profile_result = profile_subgraph.invoke({
            "user_id": user_id,
            "profile_data": {},
            "last_updated": ""
        }, config=profile_config)

        results["profile_result"] = profile_result

    if operation in ["conversation", "both"]:
        # 调用对话子图
        conv_config = {"configurable": {"thread_id": f"conversation_{user_id}"}}
        conversation_result = conversation_subgraph.invoke({
            "user_id": user_id,
            "messages": [],
            "context": {}
        }, config=conv_config)

        results["conversation_result"] = conversation_result

    results["final_status"] = "completed"
    return results

# 创建主图
def create_main_graph_with_memory():
    """创建带内存管理的主图"""
    builder = StateGraph(MainState)
    builder.add_node("coordinate", coordinate_subgraphs)
    builder.add_edge(START, "coordinate")
    builder.add_edge("coordinate", END)

    # 主图也有自己的内存
    main_memory = InMemorySaver()
    return builder.compile(checkpointer=main_memory)

main_graph = create_main_graph_with_memory()
```

### 内存状态检查

```python
def inspect_subgraph_memory():
    """检查子图内存状态"""
    print("=== 子图内存状态检查 ===")

    # 检查档案子图内存
    print("\n档案子图内存:")
    try:
        profile_config = {"configurable": {"thread_id": "profile_user123"}}
        profile_state = profile_subgraph.get_state(profile_config)

        if profile_state.values:
            print(f"  用户ID: {profile_state.values.get('user_id', '无')}")
            print(f"  档案数据: {profile_state.values.get('profile_data', {})}")
            print(f"  更新时间: {profile_state.values.get('last_updated', '无')}")
        else:
            print("  无状态数据")
    except Exception as e:
        print(f"  检查失败: {e}")

    # 检查对话子图内存
    print("\n对话子图内存:")
    try:
        conv_config = {"configurable": {"thread_id": "conversation_user123"}}
        conv_state = conversation_subgraph.get_state(conv_config)

        if conv_state.values:
            print(f"  用户ID: {conv_state.values.get('user_id', '无')}")
            print(f"  消息数量: {len(conv_state.values.get('messages', []))}")
            print(f"  上下文: {conv_state.values.get('context', {})}")
        else:
            print("  无状态数据")
    except Exception as e:
        print(f"  检查失败: {e}")

def run_memory_demo():
    """运行内存演示"""
    print("子图独立内存演示启动！")

    # 测试不同操作
    test_cases = [
        {"user_id": "user123", "operation": "profile"},
        {"user_id": "user123", "operation": "conversation"},
        {"user_id": "user456", "operation": "both"},
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== 测试案例 {i} ===")
        print(f"用户: {test_case['user_id']}, 操作: {test_case['operation']}")

        try:
            main_config = {"configurable": {"thread_id": f"main_{test_case['user_id']}"}}
            result = main_graph.invoke(test_case, config=main_config)

            print(f"执行状态: {result.get('final_status', '未知')}")

            if result.get("profile_result"):
                print("档案子图已执行")

            if result.get("conversation_result"):
                print("对话子图已执行")

        except Exception as e:
            print(f"执行错误: {e}")

    # 检查内存状态
    inspect_subgraph_memory()
```

## 🚀 高级内存管理模式

### 1. 内存同步机制

```python
class MemorySynchronizer:
    """内存同步器"""

    def __init__(self):
        self.sync_rules = {}
        self.sync_history = []

    def add_sync_rule(self, source_subgraph: str, target_subgraph: str, field_mapping: dict):
        """添加同步规则"""
        rule_id = f"{source_subgraph}_to_{target_subgraph}"
        self.sync_rules[rule_id] = {
            "source": source_subgraph,
            "target": target_subgraph,
            "mapping": field_mapping
        }
        print(f"添加同步规则: {rule_id}")

    def sync_memory(self, source_state: dict, rule_id: str) -> dict:
        """同步内存"""
        if rule_id not in self.sync_rules:
            return {}

        rule = self.sync_rules[rule_id]
        mapping = rule["mapping"]

        synced_data = {}
        for source_field, target_field in mapping.items():
            if source_field in source_state:
                synced_data[target_field] = source_state[source_field]

        # 记录同步历史
        sync_record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "rule_id": rule_id,
            "synced_fields": list(synced_data.keys())
        }
        self.sync_history.append(sync_record)

        return synced_data

    def get_sync_history(self) -> list:
        """获取同步历史"""
        return self.sync_history

# 使用同步器
synchronizer = MemorySynchronizer()

# 添加同步规则：档案 → 对话
synchronizer.add_sync_rule(
    "profile",
    "conversation",
    {"user_id": "user_id", "profile_data": "user_profile"}
)

def synchronized_subgraph_call(state: dict, subgraph, config: dict, sync_rule_id: str = None):
    """同步的子图调用"""
    # 执行子图
    result = subgraph.invoke(state, config=config)

    # 如果有同步规则，执行同步
    if sync_rule_id:
        synced_data = synchronizer.sync_memory(result, sync_rule_id)
        result.update(synced_data)

    return result
```

### 2. 分层内存架构

```python
class LayeredMemoryManager:
    """分层内存管理器"""

    def __init__(self):
        self.layers = {
            "global": InMemorySaver(),      # 全局层
            "session": InMemorySaver(),     # 会话层
            "task": InMemorySaver(),        # 任务层
            "temporary": InMemorySaver()    # 临时层
        }
        self.layer_hierarchy = ["temporary", "task", "session", "global"]

    def get_memory_for_layer(self, layer: str):
        """获取指定层的内存"""
        return self.layers.get(layer)

    def store_data(self, layer: str, namespace: tuple, key: str, value: any):
        """存储数据到指定层"""
        if layer in self.layers:
            # 注意：InMemorySaver 不直接支持 put 方法
            # 这里提供概念性实现
            print(f"存储到 {layer} 层: {namespace}/{key}")

    def retrieve_data(self, namespace: tuple, key: str, preferred_layer: str = None):
        """检索数据（按层次优先级）"""
        search_layers = [preferred_layer] if preferred_layer else self.layer_hierarchy

        for layer in search_layers:
            if layer in self.layers:
                # 尝试从该层检索
                print(f"从 {layer} 层检索: {namespace}/{key}")
                # 实际实现需要根据具体存储后端

        return None

    def cleanup_layer(self, layer: str):
        """清理指定层"""
        if layer in self.layers:
            # 重新创建该层的内存
            self.layers[layer] = InMemorySaver()
            print(f"已清理 {layer} 层")

# 使用分层内存
memory_manager = LayeredMemoryManager()

def create_layered_subgraph(layer: str):
    """创建使用指定层内存的子图"""
    memory = memory_manager.get_memory_for_layer(layer)

    def layered_node(state):
        # 使用分层内存的节点逻辑
        return {"processed": True, "layer": layer}

    builder = StateGraph(dict)
    builder.add_node("process", layered_node)
    builder.add_edge(START, "process")
    builder.add_edge("process", END)

    return builder.compile(checkpointer=memory)

# 创建不同层次的子图
global_subgraph = create_layered_subgraph("global")
session_subgraph = create_layered_subgraph("session")
task_subgraph = create_layered_subgraph("task")
```

### 3. 内存性能优化

```python
class MemoryOptimizer:
    """内存性能优化器"""

    def __init__(self):
        self.cache = {}
        self.access_patterns = {}
        self.optimization_rules = []

    def track_access(self, subgraph_name: str, operation: str):
        """跟踪访问模式"""
        if subgraph_name not in self.access_patterns:
            self.access_patterns[subgraph_name] = {
                "read_count": 0,
                "write_count": 0,
                "last_access": None
            }

        pattern = self.access_patterns[subgraph_name]

        if operation == "read":
            pattern["read_count"] += 1
        elif operation == "write":
            pattern["write_count"] += 1

        pattern["last_access"] = datetime.datetime.now()

    def suggest_optimizations(self) -> list:
        """建议优化策略"""
        suggestions = []

        for subgraph, pattern in self.access_patterns.items():
            read_ratio = pattern["read_count"] / max(1, pattern["write_count"])

            if read_ratio > 10:
                suggestions.append({
                    "subgraph": subgraph,
                    "optimization": "read_cache",
                    "reason": f"读写比例 {read_ratio:.1f}:1，建议启用读缓存"
                })

            if pattern["write_count"] > 100:
                suggestions.append({
                    "subgraph": subgraph,
                    "optimization": "batch_write",
                    "reason": f"写操作频繁 ({pattern['write_count']} 次)，建议批量写入"
                })

        return suggestions

    def apply_optimization(self, subgraph_name: str, optimization_type: str):
        """应用优化策略"""
        optimization = {
            "subgraph": subgraph_name,
            "type": optimization_type,
            "applied_at": datetime.datetime.now(),
            "status": "active"
        }

        self.optimization_rules.append(optimization)
        print(f"为 {subgraph_name} 应用优化: {optimization_type}")

    def get_optimization_report(self) -> dict:
        """获取优化报告"""
        return {
            "access_patterns": self.access_patterns,
            "active_optimizations": self.optimization_rules,
            "suggestions": self.suggest_optimizations()
        }

# 使用优化器
optimizer = MemoryOptimizer()

def optimized_subgraph_call(subgraph, state, config, subgraph_name: str):
    """优化的子图调用"""
    # 跟踪访问
    optimizer.track_access(subgraph_name, "read")

    # 执行子图
    result = subgraph.invoke(state, config=config)

    # 跟踪写入
    optimizer.track_access(subgraph_name, "write")

    return result

# 定期检查优化建议
def check_optimization_suggestions():
    """检查优化建议"""
    suggestions = optimizer.suggest_optimizations()

    if suggestions:
        print("\n=== 内存优化建议 ===")
        for suggestion in suggestions:
            print(f"子图: {suggestion['subgraph']}")
            print(f"优化: {suggestion['optimization']}")
            print(f"原因: {suggestion['reason']}")
            print()
```

## 🎯 实践练习

### 练习1：多租户内存隔离

```python
class MultiTenantMemoryManager:
    """多租户内存管理器"""

    def __init__(self):
        self.tenant_memories = {}
        self.tenant_configs = {}

    def create_tenant(self, tenant_id: str, config: dict = None):
        """创建租户"""
        if tenant_id not in self.tenant_memories:
            self.tenant_memories[tenant_id] = {
                "profile": InMemorySaver(),
                "conversation": InMemorySaver(),
                "analytics": InMemorySaver()
            }

            self.tenant_configs[tenant_id] = config or {
                "max_memory_size": "100MB",
                "retention_days": 30,
                "backup_enabled": True
            }

            print(f"创建租户: {tenant_id}")

    def get_tenant_memory(self, tenant_id: str, memory_type: str):
        """获取租户内存"""
        if tenant_id not in self.tenant_memories:
            self.create_tenant(tenant_id)

        return self.tenant_memories[tenant_id].get(memory_type)

    def create_tenant_subgraph(self, tenant_id: str, subgraph_type: str):
        """为租户创建子图"""
        memory = self.get_tenant_memory(tenant_id, subgraph_type)

        def tenant_node(state):
            # 租户特定的处理逻辑
            return {
                "tenant_id": tenant_id,
                "processed": True,
                "subgraph_type": subgraph_type
            }

        builder = StateGraph(dict)
        builder.add_node("process", tenant_node)
        builder.add_edge(START, "process")
        builder.add_edge("process", END)

        return builder.compile(checkpointer=memory)

    def cleanup_tenant(self, tenant_id: str):
        """清理租户数据"""
        if tenant_id in self.tenant_memories:
            del self.tenant_memories[tenant_id]
            del self.tenant_configs[tenant_id]
            print(f"清理租户: {tenant_id}")

    def get_tenant_stats(self) -> dict:
        """获取租户统计"""
        return {
            "total_tenants": len(self.tenant_memories),
            "tenants": list(self.tenant_memories.keys()),
            "memory_types": ["profile", "conversation", "analytics"]
        }

# 使用多租户管理器
tenant_manager = MultiTenantMemoryManager()

# 创建不同租户的子图
tenant_a_profile = tenant_manager.create_tenant_subgraph("tenant_a", "profile")
tenant_b_profile = tenant_manager.create_tenant_subgraph("tenant_b", "profile")

def test_multi_tenant():
    """测试多租户隔离"""
    # 租户A的操作
    config_a = {"configurable": {"thread_id": "tenant_a_session_1"}}
    result_a = tenant_a_profile.invoke({"data": "租户A的数据"}, config=config_a)
    print(f"租户A结果: {result_a}")

    # 租户B的操作
    config_b = {"configurable": {"thread_id": "tenant_b_session_1"}}
    result_b = tenant_b_profile.invoke({"data": "租户B的数据"}, config=config_b)
    print(f"租户B结果: {result_b}")

    # 验证隔离性
    print(f"租户统计: {tenant_manager.get_tenant_stats()}")
```

### 练习2：内存备份和恢复

```python
class MemoryBackupManager:
    """内存备份管理器"""

    def __init__(self):
        self.backup_storage = {}
        self.backup_metadata = {}

    def create_backup(self, subgraph_name: str, memory_saver, backup_id: str = None):
        """创建内存备份"""
        if backup_id is None:
            backup_id = f"{subgraph_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 注意：实际实现需要根据具体的内存保存器类型
        # 这里提供概念性实现
        backup_data = {
            "subgraph_name": subgraph_name,
            "backup_time": datetime.datetime.now().isoformat(),
            "data": "序列化的内存数据"  # 实际需要序列化内存内容
        }

        self.backup_storage[backup_id] = backup_data
        self.backup_metadata[backup_id] = {
            "subgraph": subgraph_name,
            "size": len(str(backup_data)),
            "created_at": backup_data["backup_time"]
        }

        print(f"创建备份: {backup_id}")
        return backup_id

    def restore_backup(self, backup_id: str, target_memory_saver):
        """恢复内存备份"""
        if backup_id not in self.backup_storage:
            raise ValueError(f"备份 {backup_id} 不存在")

        backup_data = self.backup_storage[backup_id]

        # 实际实现需要反序列化并恢复到目标内存保存器
        print(f"恢复备份: {backup_id}")
        print(f"备份时间: {backup_data['backup_time']}")

        return True

    def list_backups(self, subgraph_name: str = None) -> list:
        """列出备份"""
        backups = []

        for backup_id, metadata in self.backup_metadata.items():
            if subgraph_name is None or metadata["subgraph"] == subgraph_name:
                backups.append({
                    "backup_id": backup_id,
                    "subgraph": metadata["subgraph"],
                    "size": metadata["size"],
                    "created_at": metadata["created_at"]
                })

        return backups

    def cleanup_old_backups(self, days_to_keep: int = 7):
        """清理旧备份"""
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)

        to_delete = []
        for backup_id, metadata in self.backup_metadata.items():
            created_at = datetime.datetime.fromisoformat(metadata["created_at"])
            if created_at < cutoff_date:
                to_delete.append(backup_id)

        for backup_id in to_delete:
            del self.backup_storage[backup_id]
            del self.backup_metadata[backup_id]
            print(f"删除旧备份: {backup_id}")

        return len(to_delete)

# 使用备份管理器
backup_manager = MemoryBackupManager()

def demo_backup_restore():
    """演示备份和恢复"""
    # 创建备份
    backup_id = backup_manager.create_backup("profile_subgraph", profile_memory)

    # 列出备份
    backups = backup_manager.list_backups()
    print(f"可用备份: {len(backups)} 个")

    # 恢复备份
    backup_manager.restore_backup(backup_id, profile_memory)

    # 清理旧备份
    cleaned = backup_manager.cleanup_old_backups(days_to_keep=1)
    print(f"清理了 {cleaned} 个旧备份")
```

### 练习3：内存监控仪表板

```python
class MemoryDashboard:
    """内存监控仪表板"""

    def __init__(self):
        self.metrics = {}
        self.alerts = []
        self.thresholds = {
            "memory_usage": 80,  # 百分比
            "response_time": 5.0,  # 秒
            "error_rate": 5.0  # 百分比
        }

    def collect_metrics(self, subgraph_name: str, metrics: dict):
        """收集指标"""
        if subgraph_name not in self.metrics:
            self.metrics[subgraph_name] = []

        metric_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            **metrics
        }

        self.metrics[subgraph_name].append(metric_entry)

        # 检查告警
        self._check_alerts(subgraph_name, metrics)

    def _check_alerts(self, subgraph_name: str, metrics: dict):
        """检查告警条件"""
        for metric_name, threshold in self.thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]

                if value > threshold:
                    alert = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "subgraph": subgraph_name,
                        "metric": metric_name,
                        "value": value,
                        "threshold": threshold,
                        "severity": "warning" if value < threshold * 1.5 else "critical"
                    }

                    self.alerts.append(alert)
                    print(f"🚨 告警: {subgraph_name} {metric_name} = {value} (阈值: {threshold})")

    def get_dashboard_data(self) -> dict:
        """获取仪表板数据"""
        dashboard = {
            "summary": {
                "total_subgraphs": len(self.metrics),
                "active_alerts": len([a for a in self.alerts if self._is_recent_alert(a)]),
                "last_update": datetime.datetime.now().isoformat()
            },
            "subgraphs": {},
            "recent_alerts": [a for a in self.alerts if self._is_recent_alert(a)]
        }

        # 为每个子图生成摘要
        for subgraph_name, metrics_list in self.metrics.items():
            if metrics_list:
                latest_metrics = metrics_list[-1]
                dashboard["subgraphs"][subgraph_name] = {
                    "status": "healthy" if not self._has_recent_alerts(subgraph_name) else "warning",
                    "last_metrics": latest_metrics,
                    "metrics_count": len(metrics_list)
                }

        return dashboard

    def _is_recent_alert(self, alert: dict, minutes: int = 60) -> bool:
        """检查是否为最近的告警"""
        alert_time = datetime.datetime.fromisoformat(alert["timestamp"])
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
        return alert_time > cutoff_time

    def _has_recent_alerts(self, subgraph_name: str) -> bool:
        """检查子图是否有最近的告警"""
        return any(
            alert["subgraph"] == subgraph_name and self._is_recent_alert(alert)
            for alert in self.alerts
        )

    def print_dashboard(self):
        """打印仪表板"""
        data = self.get_dashboard_data()

        print("\n" + "="*50)
        print("内存监控仪表板")
        print("="*50)

        summary = data["summary"]
        print(f"子图总数: {summary['total_subgraphs']}")
        print(f"活跃告警: {summary['active_alerts']}")
        print(f"最后更新: {summary['last_update']}")

        print(f"\n子图状态:")
        for name, info in data["subgraphs"].items():
            status_icon = "✅" if info["status"] == "healthy" else "⚠️"
            print(f"  {status_icon} {name}: {info['status']}")

        if data["recent_alerts"]:
            print(f"\n最近告警:")
            for alert in data["recent_alerts"][-5:]:  # 显示最近5个
                severity_icon = "🟡" if alert["severity"] == "warning" else "🔴"
                print(f"  {severity_icon} {alert['subgraph']}: {alert['metric']} = {alert['value']}")

# 使用监控仪表板
dashboard = MemoryDashboard()

def simulate_monitoring():
    """模拟监控数据收集"""
    import random

    subgraphs = ["profile", "conversation", "analytics"]

    for _ in range(10):
        for subgraph in subgraphs:
            # 模拟指标数据
            metrics = {
                "memory_usage": random.uniform(50, 95),
                "response_time": random.uniform(0.5, 8.0),
                "error_rate": random.uniform(0, 10),
                "requests_per_second": random.uniform(10, 100)
            }

            dashboard.collect_metrics(subgraph, metrics)

        time.sleep(0.1)  # 模拟时间间隔

    # 显示仪表板
    dashboard.print_dashboard()
```

## 🔧 常见问题

### Q1: 子图内存会相互影响吗？

**答：** 不会，每个子图的内存是完全隔离的：

```python
# 子图A的内存故障不会影响子图B
try:
    result_a = subgraph_a.invoke(data, config_a)
except Exception as e:
    print(f"子图A失败: {e}")
    # 子图B仍然可以正常工作
    result_b = subgraph_b.invoke(data, config_b)
```

### Q2: 如何在子图间共享数据？

**答：** 使用共享存储或主图协调：

```python
# 方法1：共享存储
from langgraph.store.memory import InMemoryStore
shared_store = InMemoryStore()

# 方法2：主图协调
def coordinate_data_sharing(state):
    result_a = subgraph_a.invoke(state)
    # 将A的结果传递给B
    state_for_b = {**state, "shared_data": result_a}
    result_b = subgraph_b.invoke(state_for_b)
    return result_b
```

### Q3: 子图内存的性能如何优化？

**答：** 使用缓存、批处理和异步操作：

```python
# 缓存频繁访问的数据
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_subgraph_call(subgraph_id, input_hash):
    # 缓存子图调用结果
    pass

# 批处理内存操作
def batch_memory_operations(operations):
    # 批量执行内存操作
    pass
```

## 📖 相关资源

### 官方文档
- [LangGraph 检查点](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [子图组合](https://langchain-ai.github.io/langgraph/concepts/composition/)

### 下一步学习
- [13. 子图教学](13_subgraphs_tutorial.md) - 子图基础
- [06. 内存检查点教学](06_memory_checkpoint_tutorial.md) - 内存管理

### 代码示例
- 完整代码：[14_subgraph_with_memory.py](../../teach_code/14_subgraph_with_memory.py)
- 运行方式：`python teach_code/14_subgraph_with_memory.py`

## 🌟 总结

子图独立内存是构建大规模应用的关键技术：

1. **隔离性**：每个子图拥有独立的内存空间
2. **可扩展性**：支持大规模、多租户应用
3. **可维护性**：独立的状态管理和调试
4. **性能优化**：针对性的内存优化策略
5. **容错性**：单个子图故障不影响整体系统

掌握子图内存管理后，你可以构建企业级的复杂应用架构！
