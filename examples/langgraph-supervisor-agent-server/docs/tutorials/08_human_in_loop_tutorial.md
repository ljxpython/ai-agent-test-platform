# 08. 人机交互教学

## 🎯 学习目标

通过这个教程，你将学会：
- 人机交互的设计原理和应用场景
- 如何使用 interrupt 实现执行暂停
- 审批工作流的实现方法
- 人工干预的最佳实践

## 📚 核心概念

### 1. 什么是人机交互？

人机交互（Human-in-the-Loop）是指在 AI 执行过程中**暂停并等待人工输入**的机制：

```
AI 执行 → 遇到关键决策 → 暂停等待 → 人工输入 → 继续执行
```

**应用场景：**
- **敏感操作确认**：删除、重置等危险操作
- **内容审核**：发布前的人工审核
- **专家咨询**：需要专业知识的决策
- **质量控制**：关键环节的人工检查

### 2. interrupt 机制

LangGraph 使用 `interrupt` 函数实现执行暂停：

```python
from langgraph.types import interrupt

def sensitive_operation(action: str) -> str:
    """执行敏感操作（需要人工确认）"""
    # 请求人工确认
    confirmation = interrupt({
        "action": action,
        "message": f"是否确认执行操作: {action}？(yes/no)"
    })

    if confirmation.get("data", "").lower() in ["yes", "y", "是", "确认"]:
        return f"已执行操作: {action}"
    else:
        return f"操作已取消: {action}"
```

### 3. 中断处理流程

1. **触发中断**：调用 `interrupt()` 函数
2. **状态保存**：当前执行状态被保存
3. **等待输入**：系统暂停，等待人工决策
4. **恢复执行**：收到输入后继续执行

## 🔍 代码详细解析

### 基础中断工具

```python
from langgraph.types import interrupt
from langchain_core.tools import tool

@tool
def human_assistance(query: str) -> str:
    """请求人工协助"""
    # 使用 interrupt 暂停执行，等待人工输入
    human_response = interrupt({"query": query})
    return human_response.get("data", "没有收到人工回复")

@tool
def sensitive_action(action: str) -> str:
    """执行敏感操作（需要人工确认）"""
    # 请求人工确认
    confirmation = interrupt({
        "action": action,
        "message": f"是否确认执行操作: {action}？(yes/no)"
    })

    if confirmation.get("data", "").lower() in ["yes", "y", "是", "确认"]:
        return f"已执行操作: {action}"
    else:
        return f"操作已取消: {action}"

@tool
def review_content(content: str) -> str:
    """内容审核工具"""
    # 简单的内容检查
    sensitive_words = ["删除", "重置", "格式化", "清空"]

    if any(word in content for word in sensitive_words):
        # 需要人工审核
        review_result = interrupt({
            "content": content,
            "message": f"检测到敏感内容，需要人工审核: {content}"
        })

        if review_result.get("data", "").lower() in ["approve", "通过", "同意"]:
            return f"内容已通过审核: {content}"
        else:
            return f"内容被拒绝: {content}"
    else:
        return f"内容自动通过: {content}"
```

### 图构建和中断处理

```python
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver

# 设置工具
tools = [human_assistance, sensitive_action, review_content]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 创建检查点保存器（人机交互需要）
memory = InMemorySaver()

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

# 添加工具节点
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# 添加边
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

# 编译图（启用检查点以支持中断）
graph = graph_builder.compile(checkpointer=memory)
```

### 中断处理逻辑

```python
def run_human_in_loop_demo():
    """运行人机交互演示"""
    config = {"configurable": {"thread_id": "human_loop_1"}}

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        try:
            # 开始处理
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config
            )

            # 检查是否有中断
            current_state = graph.get_state(config)

            if current_state.next:
                # 有中断，等待人工输入
                print("\n=== 需要人工输入 ===")

                # 获取中断信息
                if current_state.tasks:
                    task = current_state.tasks[0]
                    if hasattr(task, 'interrupts') and task.interrupts:
                        interrupt_data = task.interrupts[0].value
                        print(f"请求: {interrupt_data}")

                # 获取人工输入
                human_input = input("请输入回复: ")

                # 继续执行
                graph.update_state(config, {"data": human_input})
                final_result = graph.invoke(None, config)

                # 输出最终回复
                if final_result.get("messages"):
                    assistant_message = final_result["messages"][-1]
                    print(f"助手: {assistant_message.content}")
            else:
                # 没有中断，直接输出回复
                if result.get("messages"):
                    assistant_message = result["messages"][-1]
                    print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")
```

## 🚀 运行演示

### 基础人机交互演示

```python
def demo_approval_workflow():
    """演示审批工作流"""
    config = {"configurable": {"thread_id": "approval_demo"}}

    # 测试用例
    test_cases = [
        "请帮我删除所有文件",  # 敏感操作
        "请审核这个内容：今天天气不错",  # 普通内容
        "我需要人工协助解决这个问题",  # 人工协助
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n=== 测试案例 {i}: {test_input} ===")

        try:
            # 处理请求
            result = graph.invoke(
                {"messages": [{"role": "user", "content": test_input}]},
                config
            )

            # 检查是否需要人工干预
            state = graph.get_state(config)

            if state.next:
                print("⏸️  需要人工干预")

                # 模拟人工输入
                if "删除" in test_input:
                    human_response = "no"  # 拒绝删除操作
                elif "协助" in test_input:
                    human_response = "我来帮助你解决问题"
                else:
                    human_response = "approve"  # 批准内容

                print(f"🤖 模拟人工输入: {human_response}")

                # 继续执行
                graph.update_state(config, {"data": human_response})
                final_result = graph.invoke(None, config)

                if final_result.get("messages"):
                    print(f"✅ 最终结果: {final_result['messages'][-1].content}")
            else:
                print("✅ 自动处理完成")
                if result.get("messages"):
                    print(f"结果: {result['messages'][-1].content}")

        except Exception as e:
            print(f"❌ 处理错误: {e}")
```

### 预期输出

```
=== 测试案例 1: 请帮我删除所有文件 ===
⏸️  需要人工干预
请求: {'action': '删除所有文件', 'message': '是否确认执行操作: 删除所有文件？(yes/no)'}
🤖 模拟人工输入: no
✅ 最终结果: 操作已取消: 删除所有文件

=== 测试案例 2: 请审核这个内容：今天天气不错 ===
✅ 自动处理完成
结果: 内容自动通过: 今天天气不错

=== 测试案例 3: 我需要人工协助解决这个问题 ===
⏸️  需要人工干预
请求: {'query': '解决这个问题'}
🤖 模拟人工输入: 我来帮助你解决问题
✅ 最终结果: 我来帮助你解决问题
```

## 🎯 高级人机交互模式

### 1. 多级审批

```python
@tool
def multi_level_approval(request: str, level: int = 1) -> str:
    """多级审批工具"""
    approval_levels = {
        1: "主管审批",
        2: "经理审批",
        3: "总监审批"
    }

    current_level_name = approval_levels.get(level, f"第{level}级审批")

    # 请求当前级别审批
    approval = interrupt({
        "request": request,
        "level": level,
        "level_name": current_level_name,
        "message": f"请求{current_level_name}: {request}"
    })

    decision = approval.get("data", "").lower()

    if decision in ["approve", "通过", "同意"]:
        if level < 3:  # 需要更高级别审批
            return multi_level_approval(request, level + 1)
        else:
            return f"请求已通过所有级别审批: {request}"
    elif decision in ["reject", "拒绝", "不同意"]:
        return f"请求在{current_level_name}被拒绝: {request}"
    else:
        return f"请求在{current_level_name}待定: {request}"

@tool
def conditional_approval(request: str, amount: float = 0) -> str:
    """条件审批工具"""
    # 根据金额确定审批级别
    if amount < 1000:
        approval_level = "自动审批"
        return f"自动审批通过: {request} (金额: {amount})"
    elif amount < 10000:
        approval_level = "主管审批"
    elif amount < 100000:
        approval_level = "经理审批"
    else:
        approval_level = "总监审批"

    # 请求相应级别审批
    approval = interrupt({
        "request": request,
        "amount": amount,
        "approval_level": approval_level,
        "message": f"请求{approval_level}: {request} (金额: {amount})"
    })

    decision = approval.get("data", "").lower()

    if decision in ["approve", "通过", "同意"]:
        return f"{approval_level}通过: {request}"
    else:
        return f"{approval_level}拒绝: {request}"
```

### 2. 专家咨询系统

```python
@tool
def expert_consultation(domain: str, question: str) -> str:
    """专家咨询工具"""
    expert_domains = {
        "技术": "技术专家",
        "法律": "法律顾问",
        "财务": "财务专家",
        "医疗": "医疗专家"
    }

    expert_type = expert_domains.get(domain, "通用专家")

    # 请求专家意见
    expert_response = interrupt({
        "domain": domain,
        "question": question,
        "expert_type": expert_type,
        "message": f"请{expert_type}回答: {question}"
    })

    expert_answer = expert_response.get("data", "专家暂时无法回复")

    return f"{expert_type}回复: {expert_answer}"

@tool
def quality_review(content: str, criteria: str = "general") -> str:
    """质量审核工具"""
    review_criteria = {
        "general": "通用质量标准",
        "technical": "技术准确性",
        "legal": "法律合规性",
        "medical": "医疗安全性"
    }

    criteria_name = review_criteria.get(criteria, criteria)

    # 请求质量审核
    review_result = interrupt({
        "content": content,
        "criteria": criteria,
        "criteria_name": criteria_name,
        "message": f"请按{criteria_name}审核以下内容: {content}"
    })

    review_decision = review_result.get("data", "").lower()

    if review_decision in ["pass", "通过", "合格"]:
        return f"质量审核通过: {content}"
    elif review_decision in ["fail", "不通过", "不合格"]:
        return f"质量审核不通过: {content}"
    else:
        return f"质量审核待定: {content}"
```

### 3. 交互式调试

```python
@tool
def debug_checkpoint(context: str) -> str:
    """调试检查点工具"""
    # 请求调试信息
    debug_info = interrupt({
        "context": context,
        "message": f"调试检查点: {context}",
        "options": ["continue", "step", "inspect", "abort"]
    })

    action = debug_info.get("data", "continue").lower()

    if action == "continue":
        return "继续执行"
    elif action == "step":
        return "单步执行"
    elif action == "inspect":
        return f"检查状态: {context}"
    elif action == "abort":
        return "中止执行"
    else:
        return f"未知调试命令: {action}"

@tool
def interactive_configuration(setting_name: str, current_value: str) -> str:
    """交互式配置工具"""
    # 请求配置更新
    config_update = interrupt({
        "setting_name": setting_name,
        "current_value": current_value,
        "message": f"当前{setting_name}设置为: {current_value}，是否需要修改？"
    })

    new_value = config_update.get("data", current_value)

    if new_value != current_value:
        return f"配置已更新: {setting_name} = {new_value}"
    else:
        return f"配置保持不变: {setting_name} = {current_value}"
```

## 🎯 实践练习

### 练习1：工作流审批系统

```python
class WorkflowApprovalSystem:
    """工作流审批系统"""

    def __init__(self):
        self.approval_rules = {
            "expense": {"threshold": 1000, "approver": "财务经理"},
            "hiring": {"threshold": 0, "approver": "人事总监"},
            "purchase": {"threshold": 5000, "approver": "采购经理"},
            "contract": {"threshold": 10000, "approver": "法务总监"}
        }

    @tool
    def submit_request(self, request_type: str, description: str, amount: float = 0) -> str:
        """提交审批请求"""
        if request_type not in self.approval_rules:
            return f"未知的请求类型: {request_type}"

        rule = self.approval_rules[request_type]

        if amount < rule["threshold"]:
            return f"自动批准: {description}"

        # 需要人工审批
        approval = interrupt({
            "request_type": request_type,
            "description": description,
            "amount": amount,
            "approver": rule["approver"],
            "message": f"请{rule['approver']}审批: {description} (金额: {amount})"
        })

        decision = approval.get("data", "").lower()

        if decision in ["approve", "通过", "同意"]:
            return f"审批通过: {description}"
        else:
            return f"审批拒绝: {description}"

# 使用示例
approval_system = WorkflowApprovalSystem()

# 测试不同类型的请求
test_requests = [
    ("expense", "差旅费报销", 800),
    ("expense", "设备采购", 1500),
    ("hiring", "招聘软件工程师", 0),
    ("purchase", "办公用品采购", 3000)
]

for req_type, desc, amount in test_requests:
    print(f"提交请求: {req_type} - {desc} - {amount}")
    # result = approval_system.submit_request(req_type, desc, amount)
    # print(f"结果: {result}")
```

### 练习2：内容审核流水线

```python
class ContentModerationPipeline:
    """内容审核流水线"""

    def __init__(self):
        self.moderation_rules = {
            "spam": ["广告", "推广", "优惠"],
            "sensitive": ["政治", "宗教", "敏感"],
            "inappropriate": ["暴力", "色情", "仇恨"]
        }

    def auto_moderate(self, content: str) -> dict:
        """自动审核"""
        issues = []

        for category, keywords in self.moderation_rules.items():
            if any(keyword in content for keyword in keywords):
                issues.append(category)

        return {
            "content": content,
            "issues": issues,
            "auto_decision": "reject" if issues else "approve"
        }

    @tool
    def moderate_content(self, content: str) -> str:
        """内容审核工具"""
        # 自动审核
        auto_result = self.auto_moderate(content)

        if auto_result["auto_decision"] == "approve":
            return f"内容自动通过: {content}"

        # 需要人工审核
        human_review = interrupt({
            "content": content,
            "issues": auto_result["issues"],
            "message": f"检测到问题: {auto_result['issues']}，请人工审核: {content}"
        })

        decision = human_review.get("data", "").lower()

        if decision in ["approve", "通过", "同意"]:
            return f"人工审核通过: {content}"
        else:
            return f"人工审核拒绝: {content}"

# 使用示例
moderation = ContentModerationPipeline()

test_contents = [
    "今天天气很好",
    "这是一个广告推广信息",
    "涉及敏感政治话题的内容"
]

for content in test_contents:
    print(f"审核内容: {content}")
    # result = moderation.moderate_content(content)
    # print(f"审核结果: {result}")
```

### 练习3：智能客服升级

```python
@tool
def escalate_to_human(issue: str, customer_info: str) -> str:
    """升级到人工客服"""
    # 分析问题复杂度
    complex_keywords = ["投诉", "退款", "法律", "紧急"]
    is_complex = any(keyword in issue for keyword in complex_keywords)

    priority = "高" if is_complex else "普通"

    # 请求人工客服介入
    human_response = interrupt({
        "issue": issue,
        "customer_info": customer_info,
        "priority": priority,
        "message": f"客服请求({priority}优先级): {issue}\n客户信息: {customer_info}"
    })

    response = human_response.get("data", "客服正在处理中，请稍候")

    return f"人工客服回复: {response}"

@tool
def request_supervisor(reason: str) -> str:
    """请求主管介入"""
    supervisor_response = interrupt({
        "reason": reason,
        "message": f"请求主管介入: {reason}"
    })

    response = supervisor_response.get("data", "主管正在处理中")

    return f"主管回复: {response}"

# 智能路由逻辑
def smart_customer_service(query: str, customer_level: str = "regular"):
    """智能客服路由"""
    # VIP 客户直接转人工
    if customer_level == "vip":
        return escalate_to_human(query, f"VIP客户: {customer_level}")

    # 复杂问题转人工
    complex_indicators = ["投诉", "不满意", "要求退款", "法律问题"]
    if any(indicator in query for indicator in complex_indicators):
        return escalate_to_human(query, f"客户级别: {customer_level}")

    # 普通问题自动回复
    return f"自动回复: 感谢您的咨询，我们会尽快处理您的问题：{query}"
```

## 🔧 常见问题

### Q1: 如何处理中断超时？

**答：** 实现超时机制和默认处理：

```python
import time
import threading

class TimeoutInterrupt:
    def __init__(self, timeout_seconds: int = 300):
        self.timeout_seconds = timeout_seconds
        self.default_response = "timeout"

    def interrupt_with_timeout(self, data: dict) -> dict:
        """带超时的中断"""
        # 设置默认响应
        result = {"data": self.default_response}

        # 实际实现中，这里会等待人工输入
        # 如果超时，返回默认响应

        return result
```

### Q2: 如何实现批量审批？

**答：** 使用批处理和批量决策：

```python
@tool
def batch_approval(items: list) -> str:
    """批量审批工具"""
    # 请求批量审批
    batch_decision = interrupt({
        "items": items,
        "count": len(items),
        "message": f"请批量审批 {len(items)} 个项目"
    })

    decisions = batch_decision.get("data", [])

    if isinstance(decisions, str):
        # 统一决策
        if decisions.lower() in ["approve_all", "全部通过"]:
            return f"批量审批通过: {len(items)} 个项目"
        else:
            return f"批量审批拒绝: {len(items)} 个项目"
    elif isinstance(decisions, list):
        # 逐项决策
        approved = sum(1 for d in decisions if d.lower() in ["approve", "通过"])
        return f"批量审批完成: {approved}/{len(items)} 个项目通过"
```

### Q3: 如何记录审批历史？

**答：** 实现审批日志系统：

```python
import datetime
import json

class ApprovalLogger:
    def __init__(self, log_file: str = "approval_log.json"):
        self.log_file = log_file
        self.logs = []

    def log_approval(self, request: dict, decision: dict, approver: str):
        """记录审批日志"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "request": request,
            "decision": decision,
            "approver": approver,
            "session_id": request.get("session_id", "unknown")
        }

        self.logs.append(log_entry)

        # 保存到文件
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2, default=str)
        except Exception as e:
            print(f"保存审批日志失败: {e}")

    def get_approval_history(self, session_id: str = None):
        """获取审批历史"""
        if session_id:
            return [log for log in self.logs if log.get("session_id") == session_id]
        return self.logs

# 使用示例
logger = ApprovalLogger()

def logged_approval(request: dict) -> str:
    """带日志的审批"""
    approval = interrupt(request)

    # 记录审批日志
    logger.log_approval(
        request=request,
        decision=approval,
        approver="human_reviewer"
    )

    return approval.get("data", "no_decision")
```

## 📖 相关资源

### 官方文档
- [LangGraph 人机交互](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)
- [中断机制](https://langchain-ai.github.io/langgraph/concepts/interrupts/)

### 下一步学习
- [09. 时间旅行教学](09_time_travel_tutorial.md) - 状态回溯
- [04. 自定义工具教学](04_custom_tools_tutorial.md) - 工具设计

### 代码示例
- 完整代码：[08_human_in_the_loop.py](../../teach_code/08_human_in_the_loop.py)
- 运行方式：`python teach_code/08_human_in_the_loop.py`

## 🌟 总结

人机交互是构建可信 AI 系统的关键：

1. **安全控制**：关键操作需要人工确认
2. **质量保证**：重要决策需要人工审核
3. **专业知识**：复杂问题需要专家介入
4. **灵活性**：可根据情况调整自动化程度
5. **可追溯性**：完整的审批和决策记录

掌握人机交互后，你可以构建安全可靠的企业级 AI 应用！
