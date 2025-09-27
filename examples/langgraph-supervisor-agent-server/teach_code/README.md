# LangGraph 实战教程代码示例

这个目录包含了 LangGraph 实战教程的所有可运行代码示例。

## 环境配置

### 1. 安装依赖

```bash
# 核心依赖
pip install langgraph langchain langchain-core
pip install langchain-deepseek langchain-openai
pip install langchain-tavily python-dotenv

# 可选依赖
pip install "langgraph[dev]"  # 可视化工具
pip install langchain-mcp-adapters  # MCP 支持
```

### 2. 环境变量配置

创建 `.env` 文件：

```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# OpenAI API (可选)
OPENAI_API_KEY=sk-your-openai-api-key

# Tavily Search API (可选)
TAVILY_API_KEY=your-tavily-api-key
```

## 代码示例列表

### 基础功能
- `01_basic_chatbot.py` - 基础聊天机器人
- `02_streaming_chatbot.py` - 流式聊天机器人
- `03_chatbot_with_tools.py` - 带搜索工具的聊天机器人
- `04_custom_tools.py` - 自定义工具集成

### 状态管理
- `05_state_management.py` - 复杂状态管理
- `06_memory_checkpoint.py` - 内存检查点
- `07_sqlite_checkpoint.py` - SQLite 检查点

### 高级特性
- `08_human_in_the_loop.py` - 人机交互
- `09_time_travel.py` - 时间旅行
- `10_runtime_context.py` - 运行时上下文

### 记忆系统
- `11_short_term_memory.py` - 短期记忆
- `12_long_term_memory.py` - 长期记忆

### 子图和模块化
- `13_subgraphs.py` - 基础子图
- `14_subgraph_with_memory.py` - 带独立内存的子图

### MCP 集成
- `15_mcp_integration.py` - MCP 客户端集成
- `16_custom_mcp_server.py` - 自定义 MCP 服务器

### 多智能体系统
- `17_multi_agent_supervisor.py` - Supervisor 模式多智能体

## 运行示例

每个文件都可以独立运行：

```bash
# 运行基础聊天机器人
python 01_basic_chatbot.py

# 运行带工具的聊天机器人
python 03_chatbot_with_tools.py

# 运行时间旅行演示
python 09_time_travel.py
```

## 注意事项

1. **API 密钥**：确保在 `.env` 文件中配置了正确的 API 密钥
2. **可选依赖**：某些示例需要额外的 API 密钥（如 Tavily）
3. **错误处理**：所有示例都包含了完善的错误处理
4. **模拟模式**：当外部服务不可用时，代码会自动回退到模拟模式

## 学习路径

建议按以下顺序学习：

1. **基础概念**：01-04（聊天机器人和工具）
2. **状态管理**：05-07（状态和检查点）
3. **高级特性**：08-10（人机交互、时间旅行、上下文）
4. **记忆系统**：11-12（短期和长期记忆）
5. **模块化**：13-14（子图）
6. **集成**：15-16（MCP）
7. **多智能体**：17（协作系统）

## 故障排除

### 常见问题

1. **导入错误**：确保安装了所有必需的依赖
2. **API 错误**：检查 API 密钥是否正确配置
3. **网络问题**：某些示例需要网络连接

### 获取帮助

如果遇到问题，请检查：
1. 环境变量配置
2. 依赖包版本
3. 网络连接
4. API 密钥有效性

每个示例都包含详细的错误信息和处理逻辑，可以帮助诊断问题。
