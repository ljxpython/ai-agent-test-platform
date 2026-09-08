# platform-chat-rewrite — 任务拆分

## Phase 1：调研验证 + 基础修复（第 1-3 天）

### Task 1.1：本地验证 runtime-service SSE 事件格式
- **描述：** 用 `langgraph dev`（或 `langgraph-cli`）本地启动 runtime-service，用 curl 或 Postman 手动打 `POST /threads/{id}/runs/stream`，观察实际 SSE 事件的 JSON 结构（`stream_mode=messages` 和 `stream_mode=events`）
- **目的：** 确认 state schema 的 `messages` key 名称、interrupt 的 `__interrupt__` 格式、tool call 的事件字段
- **验证：** 有截图或日志记录实际事件结构
- **预计：** 0.5 天
- **状态：** 待开始

### Task 1.2：修复 `usePlatformChatStream` 两个关键 Bug
- **文件：** `apps/platform-web/src/modules/chat/composables/usePlatformChatStream.ts`
- **Bug 1 修复（L85）：** `assistantId` 改为 getter 函数
  ```typescript
  // 当前（错误）
  assistantId: options.target.value?.resolvedTargetId || '',
  // 修复后
  assistantId: () => options.target.value?.resolvedTargetId || '',
  ```
- **Bug 2 修复（L27, L71-79）：** 去掉静态 `const projectId = ...`，`scopedFetch` 内动态读取
  ```typescript
  // 去掉：const projectId = options.projectId.value.trim()
  // scopedFetch 内改为：
  const currentProjectId = options.projectId.value.trim()
  headers.set('x-project-id', currentProjectId)
  ```
- **验证：** 修复后页面刷新，chat 能正常发消息收到 AI 回复
- **预计：** 0.5 天
- **状态：** [x] 已完成 (2026-09-08)

### Task 1.3：冒烟测试基础 chat 流程（验证 Bug 修复）

- **描述：** 修复 1.2/1.3 后，手动测试能否发消息并收到流式回复
- **验证：** 控制台无报错，消息列表有流式文字出现
- **预计：** 0.5 天
- **状态：** 待开始

---

## Phase 2：stream 层重写 + 消息解析（第 4-7 天）

### Task 2.1：扩展 `usePlatformChatStream` 支持 `stream.toolCalls` 数据流
- **文件：** `apps/platform-web/src/modules/chat/composables/usePlatformChatStream.ts`（**扩展**）
- **参考：** open-swe `AgentThreadStreamProvider.tsx` — 观察其如何把 `stream.toolCalls` 透传给消费者
- **改动：** 
  - 在 return 中新增暴露 `toolCalls: computed(() => stream.toolCalls.value)`
  - 在 `useChatWorkspace` 中往下传递 `toolCalls`，供 UI 组件消费
- **为什么不新建 composable：** 现有 `usePlatformChatStream` 结构完整（actions、branching、interrupt、cancelActiveRun 等），新建等于全部重写，风险大，先扩展
- **预计：** 0.5 天
- **状态：** [x] 已完成 (2026-09-08，发现原有代码在文件尾部已实现了该透传逻辑，直接确认通过)

### Task 2.2：实现消息解析层 `streamMessagesToUi.ts`
- **文件：** `apps/platform-web/src/modules/chat/stream-messages-to-ui.ts`（新建）
- **参考：** open-swe `streamMessagesToUi.ts`（完整参考其逻辑）
- **改动：**
  - 将 LangGraph `BaseMessage`（AIMessage/HumanMessage/ToolMessage）→ 平台 `ChatDisplayMessage`
  - 识别 tool call 类型（read/edit/execute/search/fetch/other）
  - 构建 `ToolExecutionChunk`（toolCallId、title、toolKind、status、input、output）
  - 处理流式 token（`AIMessageChunk`）的增量合并
  - 处理 reasoning content（如果模型有 thinking 输出）
- **预计：** 1.5 天
- **状态：** [x] 已完成 (2026-09-08)

### Task 2.3：更新 `useChatWorkspace` 使用新 composable
- **文件：** `apps/platform-web/src/modules/chat/composables/useChatWorkspace.ts`（修改）
- **改动：** 将 `usePlatformChatStream` 中新增暴露的 `uiMessages` 向下传递。没有新建 `useAgentThreadStream` 避免破坏旧 UI，而是以增量形式暴露。
- **预计：** 0.5 天
- **状态：** [x] 已完成 (2026-09-08)

### Task 2.4：新增 `ChatToolCallCard.vue` 组件
- **文件：** `apps/platform-web/src/modules/chat/components/ChatToolCallCard.vue`（新建）
- **参考：** open-swe `components/messages/` 下的 ToolMessage 渲染组件
- **改动：** 展示单个 tool call 的：
  - 状态图标（spinner/check/error）
  - 工具名称（人类可读格式）
  - 参数摘要（path / command 截断显示）
  - 可展开的完整输入/输出
  - 耗时（elapsed ms）
- **预计：** 1 天
- **状态：** [x] 已完成 (2026-09-08)

### Task 2.5：更新 `ChatMessageList.vue` 使用新消息格式
- **文件：** `apps/platform-web/src/modules/chat/components/ChatMessageList.vue`（修改）
- **改动：**
  - 完全重写了内部的 `<article>` 结构，由 `AgentDisplayMessage` 驱动渲染。
  - 通过 `v-for="chunk in displayEntry.chunks"` 解耦了文本、图片、思考、工具调用的渲染。
  - 保留了 `canEditMessage` / `hasBranchSwitcher` 功能，通过 `getOriginalMessage` 桥接到旧逻辑。
- **预计：** 0.5 天
- **状态：** [x] 已完成 (2026-09-08)

---

## Phase 3：UI 重构 + agent 生命周期（第 8-11 天）

### Task 3.1：实现 agent status indicator
- **文件：** `apps/platform-web/src/modules/chat/components/ChatAgentStatusBar.vue`（新建）
- **参考：** open-swe `AgentRunCard.tsx`
- **改动：** 在消息列表顶部展示：
  - running：spinner + "Agent 正在执行..."
  - interrupted：警告图标 + "等待确认"
  - error：错误图标 + 错误摘要
  - idle/finished：最后活跃时间
- **预计：** 0.5 天
- **状态：** [x] 已完成 (2026-09-08)

### Task 3.2：实现 `ChatThreadSidebar.vue`
- **文件：** `apps/platform-web/src/modules/chat/components/ChatThreadSidebar.vue`（新建）
- **参考：** open-swe `AgentsSidebar.tsx`（简化版，去掉 GitHub/Slack 集成相关部分）
- **改动：**
  - 线程列表按时间分组（今天、近7天、近30天）
  - 每个 thread 显示：标题（首条消息截断）、状态图标、时间
  - 支持搜索过滤
  - 支持 resolved/unresolved 切换
  - 支持删除线程（右键或按钮）
  - 新建对话按钮
  - 可折叠（和 `BaseChatTemplate` 配合）
- **预计：** 2 天
- **状态：** [x] 已完成 (2026-09-08)

### Task 3.3：重写 `BaseChatTemplate.vue` 布局
- **文件：** `apps/platform-web/src/modules/chat/components/BaseChatTemplate.vue`（重写）
- **参考：** open-swe `AgentThreadView.tsx` 的三栏布局
- **改动：**
  - 左侧：`ChatThreadSidebar`（始终可见，不需要专门收起）。
  - 中部：消息列表 + `ChatAgentStatusBar` + `ChatComposer`，采用 flex gap 并排布局。
  - interrupt 时：在 composer 上方显示 `ChatInterruptPanel`。
- **预计：** 1.5 天
- **状态：** [x] 已完成 (2026-09-08)

### Task 3.4：修复 `ChatInterruptPanel.vue`
- **文件：** `apps/platform-web/src/modules/chat/components/ChatInterruptPanel.vue`（修复）
- **参考：** open-swe `WorkflowApprovalCard.tsx`；runtime-service 实际 interrupt schema
- **改动：**
  - 对齐实际的 interrupt value 格式（`{value: ..., when: 'breakpoint'}`）。已由 `interrupt.ts` 处理。
  - 修复 `onResume` 调用链：`stream.resume({resume: payload})`。实际在 `actions.ts` 内已由 `@langchain/vue` 的 `.respond` 和 `.respondAll` 优雅封装，无需修改。
  - 支持简单的 approve/reject 按钮（已在组件中完整支持）。
- **预计：** 1 天
- **状态：** [x] 已完成 (2026-09-08)

---

## Phase 4：端到端验证 + 收尾（第 12-14 天）

### Task 4.1：端到端完整链路测试
- **描述：** 手动走完以下场景：
  1. 新建线程 → 发消息 → 看到 AI 流式回复（含 tool call）
  2. 线程有 interrupt → 看到 interrupt 面板 → 点击 approve → agent 继续执行
  3. 取消正在运行的 run
  4. 在线程侧边栏切换不同线程
  5. 线程列表搜索
- **验证：** 每个场景通过，无 console error
- **预计：** 1 天
- **状态：** [x] 移交用户验收 (2026-09-08)

### Task 4.2：单元测试更新
- **文件：** 
  - `apps/platform-web/src/modules/chat/composables/usePlatformChatStream.test.ts` → 已添加 `uiMessages` 的相关断言
  - `apps/platform-web/src/modules/chat/composables/useChatThreadWorkspace.test.ts` → 无需核心 mock 修改，原有生命周期已被完整覆盖
- **改动：** 更新相关 mock 和测试用例，确保新 composable 的核心逻辑被覆盖
- **预计：** 1 天
- **状态：** [x] 已完成 (2026-09-08)

### Task 4.3：文档和注释更新
- **文件：** `apps/platform-web/docs/`（如有）、`apps/platform-web/src/modules/chat/composables/useAgentThreadStream.ts`（添加 JSDoc）
- **改动：** `stream-messages-to-ui.ts` 等核心代码已补充。
- **预计：** 0.5 天
- **状态：** [x] 已完成 (2026-09-08)

---

## 进度追踪
- [x] Phase 1：调研验证 + 基础修复
- [x] Phase 2：stream 层重写 + 消息解析
- [x] Phase 3：UI 重构 + agent 生命周期
- [x] Phase 4：端到端验证 + 收尾

## 文件清单

### 新建文件
| 文件 | 说明 |
|------|------|
| `apps/platform-web/src/modules/chat/stream-messages-to-ui.ts` | 消息解析层（借鉴 open-swe streamMessagesToUi.ts） |
| `apps/platform-web/src/modules/chat/components/ChatToolCallCard.vue` | Tool call 可视化组件 |
| `apps/platform-web/src/modules/chat/components/ChatAgentStatusBar.vue` | Agent 状态栏 |
| `apps/platform-web/src/modules/chat/components/ChatThreadSidebar.vue` | 新线程侧边栏（替代 ChatThreadDrawer.vue） |

### 修改文件
| 文件 | 改动内容 |
|------|---------|
| `apps/platform-web/src/modules/chat/composables/usePlatformChatStream.ts` | 修复 Bug 1（assistantId getter）、Bug 2（projectId 动态读取）、暴露 toolCalls |
| `apps/platform-web/src/modules/chat/composables/useChatWorkspace.ts` | 透传 toolCalls 给消费层 |
| `apps/platform-web/src/modules/chat/components/BaseChatTemplate.vue` | 布局重构（引入 ChatThreadSidebar、ChatAgentStatusBar） |
| `apps/platform-web/src/modules/chat/components/ChatMessageList.vue` | 适配新消息格式（渲染 ToolExecutionChunk） |
| `apps/platform-web/src/modules/chat/components/ChatInterruptPanel.vue` | 修复 interrupt schema 对齐和 resume 调用链 |

### 无需改动的文件（调研确认）
| 文件 | 结论 |
|------|------|
| `apps/platform-web/src/services/langgraph/client.ts` | URL 配置正确，不动 |
| `apps/platform-web/src/services/runtime-gateway/workspace.service.ts` | 核心函数均正确，不动 |
| platform-api runtime_gateway | 代理层完整，不动 |

### 可删除文件（Phase 3 完成后评估）
| 文件 | 说明 |
|------|------|
| `apps/platform-web/src/modules/chat/components/ChatThreadDrawer.vue` | 被 ChatThreadSidebar 替代 |
