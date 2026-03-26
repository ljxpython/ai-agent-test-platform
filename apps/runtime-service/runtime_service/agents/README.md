# runtime_service 智能体开发手册

这份文档用于统一 `runtime_service/agents` 下的智能体开发方式：

- 原则：简单、可维护、薄封装
- 目标：新增一个 agent 时，最少改动、最快可跑、可测试

## 1. 先记住这 5 条开发原则

1. 不做过度抽象：优先复用已有 `runtime`、`tools`、`model` 链路。
2. graph 文件只做装配：解析配置、构建模型、调用 agent、错误兜底。
3. 能静态就静态：prompt、tool 清单、step 配置尽量显式定义。
4. 默认可本地运行：不依赖外部复杂设施（如 Slack）才能工作。
5. 每新增一个 demo，必须同步注册、文档、测试。

## 2. 标准目录结构（推荐）

每个智能体目录建议保持以下文件：

```text
agents/<your_agent>/
  __init__.py
  graph.py
  prompts.py
  tools.py              # 如果不需要工具可省略
```

- `__init__.py`：只导出 `graph`
- `prompts.py`：只放 prompt 常量
- `tools.py`：工具、状态结构、构建函数（如 `build_xxx_agent`）
- `graph.py`：统一运行时入口（工厂函数或图编排入口）

## 3. graph.py 的推荐写法（按场景选型）

默认优先工厂函数直返 agent（`create_agent` / `create_deep_agent`），仅在需要显式多节点路由时使用 `StateGraph`。

### 3.1 默认模板（工厂函数）

1. 工厂签名使用 `make_graph(config: RunnableConfig, runtime: ServerRuntime)`
2. `merge_trusted_auth_context + build_runtime_config` 生成运行时配置
3. `resolve_model + apply_model_runtime_params` 构建模型
4. 组装工具（动态 + 必备）
5. 返回 `create_agent(...)` 或 `create_deep_agent(...)`
6. `graph = make_graph`（保持 `langgraph.json` 可继续使用 `:graph`）

### 3.2 何时保留 StateGraph

- 需要多节点/条件路由/聚合
- 需要显式状态机流程编排
- 需要在图层表达复杂分支而不仅是单 agent 调用

注意：

- 不强行统一一种模式，按业务场景选择 `create_agent` / `StateGraph` / `deepagent`
- 工厂函数里避免重初始化，减少 `Slow graph load` 风险
- `langgraph dev` 托管场景不要手动注入本地 checkpointer

## 4. 新增智能体时必须改的 4 个位置

1. `runtime_service/langgraph.json`
   - 在 `graphs` 增加 `<graph_id>: ./runtime_service/agents/<agent>/graph.py:graph`
   - 或直接导出 `make_graph` 并用 `:make_graph`
   - 如需在 `langgraph dev` 的 assistants 查询中显示说明，可用对象形式：`"<graph_id>": {"path": "...:graph", "description": "..."}`
2. `runtime_service/agents/__init__.py`
   - 增加导入和 `__all__` 导出
3. `runtime_service/docs/README.md`
   - 增加该 demo 的用途说明（1-3 条）
4. `runtime_service/tests/`
   - 增加最小测试（工具行为 + graph 注册断言）

## 5. 测试最小模板

每个 demo 至少建议包含：

1. 工具或配置行为测试（例如返回结构、关键字段）
2. `langgraph.json` 注册测试：
   - 断言 `graphs` 中包含新 graph id
3. 可选：agent 构建可用性测试（`hasattr(agent, "invoke")`）

## 6. 验证命令（提交前必跑）

在仓库根目录运行：

```bash
uv run pytest runtime_service/tests -q
uv run python -m compileall runtime_service
```

如果改了 Python 代码，再补充：

- 逐文件 `lsp_diagnostics` 无 error

## 7. 命名约定

- 目录名：`<domain>_agent`（如 `skills_sql_assistant_agent`）
- graph id：`<domain>_demo`（如 `skills_sql_assistant_demo`）
- 构建函数：`build_<domain>_agent`

## 8. 常见坑

1. 只加了 agent 文件，没注册 `langgraph.json`。
2. graph 能跑，但 `agents/__init__.py` 没导出。
3. 工具逻辑改了，没加对应测试。
4. 引入外部集成（如 Slack）导致本地不可用。

---

按这份手册开发，新增一个智能体通常只需要：

- 新建一个 agent 目录
- 改 3 个注册/文档文件
- 补 1 个测试文件

这样可以持续保持 `runtime_service` 的“薄封装、低复杂度、易迭代”。
