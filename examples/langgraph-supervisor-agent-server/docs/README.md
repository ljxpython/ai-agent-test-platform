# LangChain Supervisor Agent 实战案例

## 项目概述

这是一个基于 **LangChain** 和 **LangGraph** 的多智能体协作系统实战案例，展示了如何构建一个生产级的 AI 智能体团队。项目采用 **Supervisor 模式**，通过监督者智能体协调多个专门化的子智能体，实现复杂任务的自动分解、分配和执行。

### 🎯 核心特性

- **多智能体协作**：三个专门化智能体分工合作
- **Supervisor 模式**：集中式任务调度和管理
- **MCP 集成**：通过 Model Context Protocol 集成外部工具
- **异步处理**：支持流式处理和实时响应
- **模块化设计**：清晰的架构分层和配置管理
- **生产就绪**：完善的错误处理和日志记录

### 🤖 智能体团队

| 智能体 | 职责 | 工具集成 |
|--------|------|----------|
| **研究智能体** | 信息搜索、数据收集 | 智谱搜索、Search1API |
| **数学智能体** | 数值计算、统计分析 | 本地数学工具包 |
| **图表智能体** | 数据可视化、图表生成 | Chart MCP 服务 |
| **监督者智能体** | 任务协调、流程管理 | LangGraph Supervisor |

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd 2025-09-05-supervisor-agent-server

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
# 必需配置
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 可选配置（完整功能）
ZHIPU_API_KEY=your-zhipu-api-key
SEARCH1API_KEY=your-search1api-key
CHART_MCP_URL=http://localhost:1122/sse
```

### 3. 运行示例

```bash
# 运行基础示例
python example/graph.py

# 或使用 Agent 模块
python -c "
import asyncio
from agent.supervisor import SupervisorService

async def main():
    service = SupervisorService()
    await service.start()
    supervisor = service.get_supervisor()

    request = '请查找2024年中国GDP数据并计算增长率'
    async for result in supervisor.process_request(request):
        print(result)

asyncio.run(main())
"
```

## 📋 使用示例

### 综合任务处理

```python
user_request = """
请按以下步骤完成任务：
1. 查找2024年北京和上海的GDP数据
2. 计算上海GDP占全国GDP的比重
3. 为这些数据生成可视化图表
"""

# 系统自动执行：
# 1. 监督者分析任务 → 识别需要搜索、计算、可视化
# 2. 调用研究智能体 → 搜索GDP数据
# 3. 调用数学智能体 → 计算比重和统计
# 4. 调用图表智能体 → 生成可视化图表
# 5. 返回完整结果
```

### 单一任务处理

```python
# 信息搜索
"请搜索2024年全球AI市场规模数据"

# 数学计算
"计算100亿和80亿的差值和百分比"

# 图表生成
"为以下数据生成柱状图：北京GDP 4万亿，上海GDP 4.7万亿"
```

## 🏗️ 项目架构

```
用户请求
    ↓
监督者智能体 (Supervisor)
    ↓
┌─────────────┬─────────────┬─────────────┐
│ 研究智能体   │ 数学智能体   │ 图表智能体   │
│ (Research)  │ (Math)      │ (Chart)     │
└─────────────┴─────────────┴─────────────┘
    ↓           ↓           ↓
┌─────────────┬─────────────┬─────────────┐
│ MCP工具集成  │ 本地数学工具 │ MCP图表服务  │
│ • 智谱搜索   │ • 四则运算   │ • 图表生成器 │
│ • 网络搜索   │ • 百分比     │ • 可视化API │
└─────────────┴─────────────┴─────────────┘
```

### 核心模块

```
agent/
├── __init__.py
├── supervisor.py      # 监督者智能体实现
├── agents.py         # 智能体工厂和管理
├── config.py         # 配置管理
├── exceptions.py     # 异常定义
└── logging_config.py # 日志配置

example/
└── graph.py          # 使用示例

docs/
├── README.md                           # 项目说明
├── quick-start-guide.md               # 快速开始
└── langchain-supervisor-agent-guide.md # 详细教程
```

## 🔧 技术栈

- **LangChain**: AI 应用开发框架
- **LangGraph**: 多智能体工作流编排
- **DeepSeek**: 大语言模型
- **MCP**: Model Context Protocol 工具集成
- **Python**: 异步编程和现代 Python 特性

## 📚 学习资源

### 文档指南

1. **[快速开始指南](docs/quick-start-guide.md)** - 5分钟上手运行
2. **[详细教程](docs/langchain-supervisor-agent-guide.md)** - 深入理解原理和实现
3. **代码示例** - `example/` 目录中的实际案例

### LangChain 核心概念

- **智能体 (Agents)**: 使用 LLM 进行推理和决策的系统
- **工具 (Tools)**: 智能体可以调用的外部功能
- **链 (Chains)**: 组合多个组件的工作流
- **内存 (Memory)**: 维护对话历史和状态

### 多智能体系统

- **协调模式**: Supervisor、P2P、Hierarchical
- **通信机制**: 消息传递、共享状态、事件驱动
- **任务分配**: 基于能力、负载均衡、优先级

## 🛠️ 开发指南

### 添加新智能体

```python
# 1. 配置定义
new_agent_config = AgentConfig(
    name="translator_agent",
    description="专门负责翻译的智能体",
    prompt="你是一个专业的翻译智能体..."
)

# 2. 工厂实现
class TranslationAgentFactory(AgentFactory):
    async def create_agent(self, config):
        tools = await self._get_translation_tools()
        return create_react_agent(model=llm, tools=tools, ...)

# 3. 集成到系统
async def create_translation_agent(self):
    factory = TranslationAgentFactory(self.llm_model)
    return await factory.create_agent(config.agents["translation"])
```

### 集成外部工具

```python
# MCP 服务集成
mcp_config = MCPServerConfig(
    name="weather-service",
    transport="sse",
    url="https://api.weather.com/mcp/sse"
)

# 本地工具集成
def custom_tool(input_data: str) -> str:
    """自定义工具描述"""
    # 工具实现逻辑
    return result

tools = [custom_tool, other_tools...]
```

### 自定义监督者策略

```python
class CustomSupervisor(SupervisorAgent):
    async def _route_task(self, task_type, context):
        """自定义任务路由逻辑"""
        if task_type == "urgent":
            return await self._priority_routing(context)
        elif task_type == "batch":
            return await self._parallel_routing(context)
        else:
            return await self._sequential_routing(context)
```

## 🔍 常见问题

### Q: 如何处理 API 限流？

```python
# 添加重试和限流控制
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10)
)
async def api_call_with_retry():
    # API 调用逻辑
    pass
```

### Q: 如何监控系统性能？

```python
# 获取系统状态
status = supervisor.get_system_status()
print(f"活跃智能体: {status['agents_count']}")
print(f"可用工具: {status['mcp_servers']}")
```

### Q: 如何自定义智能体行为？

修改 `agent/config.py` 中的 prompt 配置：

```python
custom_prompt = """
你是一个专门的智能体，具有以下特点：
- 专业领域：...
- 工作方式：...
- 输出格式：...
"""
```

## 🚀 部署建议

### 开发环境

```bash
# 虚拟环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 生产环境

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### 环境变量

```bash
# 生产配置
export DEEPSEEK_API_KEY="prod-key"
export LOG_LEVEL="INFO"
export MAX_CONCURRENT_REQUESTS="10"
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - 强大的 AI 应用开发框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 多智能体工作流编排
- [DeepSeek](https://www.deepseek.com/) - 优秀的大语言模型服务

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发起 Discussion
- 邮件联系：[your-email@example.com]

---

**开始你的 LangChain 多智能体开发之旅！** 🚀
