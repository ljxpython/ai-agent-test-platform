# LangChain Supervisor Agent 快速开始指南

## 项目简介

这是一个基于 LangChain 和 LangGraph 的多智能体协作系统，通过 Supervisor 模式实现任务的智能分配和执行。系统包含三个专门化的智能体：

- **研究智能体**：负责信息搜索和数据收集
- **数学智能体**：负责数值计算和统计分析
- **图表智能体**：负责数据可视化和图表生成

## 快速安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd 2025-09-05-supervisor-agent-server
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
# 必需配置
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 可选配置（用于完整功能）
ZHIPU_API_KEY=your-zhipu-api-key
SEARCH1API_KEY=your-search1api-key
CHART_MCP_URL=http://localhost:1122/sse
```

## 快速运行

### 方式一：运行示例脚本

```bash
cd example
python graph.py
```

### 方式二：使用 Agent 模块

```python
import asyncio
from agent.supervisor import SupervisorService

async def main():
    # 启动服务
    service = SupervisorService()
    await service.start()

    # 获取监督者
    supervisor = service.get_supervisor()

    # 处理请求
    request = "请查找2024年中国GDP数据，并计算同比增长率"

    async for result in supervisor.process_request(request):
        print(result)

# 运行
asyncio.run(main())
```

## 基本使用示例

### 1. 信息搜索任务

```python
request = "请搜索2024年全球AI市场规模数据"
```

**执行流程：**
1. 监督者分析任务类型
2. 调用研究智能体搜索信息
3. 返回搜索结果

### 2. 数据计算任务

```python
request = "如果A公司营收100亿，B公司营收80亿，请计算A公司比B公司多多少百分比"
```

**执行流程：**
1. 监督者识别为计算任务
2. 调用数学智能体进行计算
3. 返回计算结果

### 3. 综合任务（搜索+计算+可视化）

```python
request = """
请完成以下任务：
1. 查找2024年北京和上海的GDP数据
2. 计算两城市GDP差值和比例
3. 生成对比图表
"""
```

**执行流程：**
1. 研究智能体搜索GDP数据
2. 数学智能体计算差值和比例
3. 图表智能体生成可视化图表

## 配置说明

### LLM 配置

```python
# 在 agent/config.py 中修改
LLM_PROVIDER = "deepseek"  # 或 "openai", "anthropic" 等
LLM_MODEL = "deepseek-chat"
LLM_TEMPERATURE = 0.0  # 控制输出随机性
```

### 智能体提示词自定义

```python
# 修改 agent/config.py 中的 prompt 字段
research_prompt = """
你是一个专门负责查找信息的研究智能体。
你的职责：
- 搜索最新、准确的信息
- 提供可靠的数据来源
- 专注于事实性内容
"""
```

### MCP 服务配置

```python
# 添加新的 MCP 服务
"new_service": MCPServerConfig(
    name="new-mcp-service",
    transport="sse",  # 或 "stdio"
    url="https://api.example.com/mcp/sse"
)
```

## 常见问题

### Q1: 如何添加新的智能体？

1. 在 `agent/config.py` 中添加智能体配置
2. 在 `agent/agents.py` 中实现创建方法
3. 在监督者配置中添加智能体引用

### Q2: 如何集成自定义工具？

```python
# 创建自定义工具
def custom_tool(input_text: str) -> str:
    """自定义工具描述"""
    # 工具逻辑
    return result

# 在 LocalToolAgentFactory 中使用
tools = [custom_tool, other_tools...]
```

### Q3: 如何处理错误和重试？

系统内置了错误处理机制，可以通过配置调整：

```python
# 在创建智能体时添加重试配置
@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10)
)
async def create_agent_with_retry():
    # 智能体创建逻辑
    pass
```

### Q4: 如何监控系统状态？

```python
# 获取系统状态
supervisor = service.get_supervisor()
status = supervisor.get_system_status()
print(status)

# 输出示例：
# {
#     "supervisor_initialized": True,
#     "agents_count": 3,
#     "available_agents": ["research", "math", "chart"],
#     "llm_model": "deepseek:deepseek-chat",
#     "mcp_servers": ["zhipu_search", "chart_generator"]
# }
```

## 性能优化建议

### 1. 异步处理

```python
# 使用异步处理提高响应速度
async def batch_process(requests):
    tasks = [supervisor.process_request(req) for req in requests]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 连接复用

```python
# 复用 MCP 连接减少开销
class ConnectionManager:
    def __init__(self):
        self._connections = {}

    async def get_connection(self, server_name):
        if server_name not in self._connections:
            self._connections[server_name] = await create_connection(server_name)
        return self._connections[server_name]
```

### 3. 缓存机制

```python
# 缓存常用查询结果
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    # 搜索逻辑
    return results
```

## 扩展开发

### 添加新智能体类型

```python
# 1. 定义智能体配置
new_agent_config = AgentConfig(
    name="translator_agent",
    description="翻译智能体",
    prompt="你是专业的翻译智能体..."
)

# 2. 实现创建方法
async def create_translator_agent(self):
    # 集成翻译工具
    translation_tools = await get_translation_tools()
    factory = LocalToolAgentFactory(self.llm_model, translation_tools)
    return await factory.create_agent(new_agent_config)

# 3. 更新监督者配置
supervisor_prompt += "\n4. translator_agent: 用于文本翻译任务"
```

### 集成外部 API

```python
# 创建 API 工具包装器
class WeatherAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_weather(self, city: str) -> str:
        """获取城市天气信息"""
        # API 调用逻辑
        return weather_data

# 集成到智能体
weather_tools = [WeatherAPI(api_key).get_weather]
weather_agent = create_react_agent(model=llm, tools=weather_tools)
```

## 部署建议

### 开发环境

```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

pip install -r requirements.txt
python example/graph.py
```

### 生产环境

```bash
# 使用 Docker 部署
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量管理

```bash
# 生产环境配置
export DEEPSEEK_API_KEY="your-production-key"
export LOG_LEVEL="INFO"
export MAX_CONCURRENT_REQUESTS="10"
export CACHE_TTL="3600"
```

## 下一步学习

1. **深入理解 LangChain**：学习更多 LangChain 组件和模式
2. **多智能体设计**：研究不同的协调机制和通信模式
3. **性能优化**：学习异步编程和系统优化技巧
4. **生产部署**：了解监控、日志和错误处理最佳实践

## 获取帮助

- 查看详细文档：`docs/langchain-supervisor-agent-guide.md`
- 查看代码示例：`example/` 目录
- 检查配置文件：`agent/config.py`
- 查看日志输出了解系统运行状态

开始你的 LangChain 多智能体开发之旅吧！
