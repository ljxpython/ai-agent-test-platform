# LangGraph 官方模型对齐使用说明

## 目标

采用 LangGraph 官方推荐的主链路：`assistant -> thread -> run`，项目层只做薄封装（租户/项目/环境管理）。

## 页面职责（前端）

- `Projects`：项目作用域入口。
- `Assistants`（原 Agents）：维护项目内 assistant profile（名称、graph_id 等）。
- `Environments`（原 Runtime）：维护环境到执行端点的映射（dev/staging/prod）。
- `Chat`：基于当前 project + assistant + environment 发起会话与运行。

## 标准使用链路

1. 先选择 `Tenant` 与 `Project`。
2. 在 `Assistants` 页面创建或选择 assistant profile。
3. 在 `Environments` 页面配置环境映射（例如 `dev -> runtime endpoint`）。
4. 进入 `Chat` 页面发起会话：
   - 创建/复用 `thread`。
   - 以 `assistant_id` 发起 `run`。

## 与官方概念映射

- 平台 `assistant profile`：对齐 LangGraph 的 assistant 配置入口。
- 平台 `environment mapping`：对齐不同部署环境（endpoint/执行目标）管理。
- Chat 执行：对齐 `threads/{thread_id}/runs/stream` 或 `runs/stream`。

## 团队约定

- 新功能优先按官方对象模型设计，不引入额外概念层。
- 兼容层不是目标，保持模型清晰优先。
- 浏览器侧请求优先走代理地址（例如 `localhost:2024` 或同源 `/api`），避免直接跨域访问 runtime。
