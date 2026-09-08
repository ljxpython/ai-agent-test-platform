# platform-chat-rewrite — 整体方案

## 背景

runtime-service 进行了一次重构（新增了 middleware 层、runtime 鉴权体系、reference agent 等），导致平台侧的对话功能出现异常。同时，原来的聊天 UI 功能较弱，无法展示 agent 的生命周期活动（tool call 执行、interrupt 请求、子任务等）。

本次借鉴 open-swe 的官方实现（`/Users/lijiaxin/PyCharmMiscProject/research/open-swe`），以其 chat 体验为蓝图，对平台层对话功能进行完全重写。

## 目标

1. **修复流式通信问题**：重写 `usePlatformChatStream` 及相关 composable，确保与 runtime-service（LangGraph API Server）的 SSE 流稳定工作
2. **实现 open-swe 级别的 agent 交互体验**：
   - 实时展示 agent 当前状态（running / interrupted / idle / error）
   - 实时展示 tool call 执行过程（工具名、参数、结果、耗时）
   - 支持 interrupt / human-in-the-loop 确认面板
   - thread 列表侧边栏（可折叠，支持搜索、状态筛选）
3. **保持现有鉴权体系不变**：继续通过 platform-api runtime_gateway 代理，携带 delegation token

## 方案设计

### 整体架构

```
用户浏览器 (platform-web Vue 3)
  │
  │  HTTP / SSE (经过 platform-api 代理)
  ▼
platform-api /api/langgraph/* (runtime_gateway)
  │  delegation token 注入
  ▼
runtime-service (LangGraph API Server)
  │  LangGraph SSE stream (stream_mode=events | messages-tuple)
  ▼
reference_agent / workflow_demo graph
```

### 核心问题诊断（调研结论）

#### Bug 1（最关键）：`assistantId` 在 composable 初始化时静态求值

**位置：** `usePlatformChatStream.ts` L85

```typescript
// 当前代码 — 问题：options.target.value 在 useStream() 调用时一次性求值，非响应式！
const stream = useStream<ChatState>({
  assistantId: options.target.value?.resolvedTargetId || '',  // ← BUG
  ...
})
```

`options.target` 是 `ComputedRef<ChatResolvedTarget | null>`，composable 创建时 `target.value` 可能还未就绪（project 信息还在加载），导致 `assistantId` 被设置为空字符串 `''`。后续 `target` 变化后 `useStream` 也感知不到。

**正确做法：** 传 getter 函数：`assistantId: () => options.target.value?.resolvedTargetId || ''`

---

#### Bug 2：`projectId` 在 composable 初始化时静态求值

**位置：** `usePlatformChatStream.ts` L27, L71-79

```typescript
// L27：初始化时固定读取
const projectId = options.projectId.value.trim()

// L71-79：scopedFetch 里用的是上面那个固定值，projectId 变化后 x-project-id header 不更新
const scopedFetch: typeof fetch = (input, init) => {
  headers.set('x-project-id', projectId)  // ← 静态值
}
```

**正确做法：** 在 `scopedFetch` 内每次调用时动态读取 `options.projectId.value.trim()`

---

#### Bug 3：消息解析层未利用 `stream.toolCalls`（`AssembledToolCall[]`）

**位置：** `helpers.ts` L246-251

```typescript
// 当前：简单粗暴地把 BaseMessage 转成旧格式，丢失了所有 tool call 状态
export function toLegacyMessage(message: BaseMessage): Message {
  return {
    ...((message.toDict().data as unknown) as Record<string, unknown>),
    type: message.getType() as Message['type']
  } as Message
}
```

`@langchain/vue` 的 `useStream` 暴露了 `stream.toolCalls: AssembledToolCall[]`，可获取每个 tool call 的实时状态（pending/in_progress/finished/error）和输出。open-swe 的 `streamMessagesToUi.ts` 完整利用了这个 API，我们的实现完全没用上，导致：tool call 没有展示、状态无法追踪、用户看不到 agent 在做什么。

---

#### Bug 4：`reconcileMissedTerminal` 轮询存在时序风险

**位置：** `usePlatformChatStream.ts` L38-68

250ms 轮询检查 run 状态，最多 20 次（5 秒）。runtime-service 重构后如果 run 终止更快或错误更快，轮询可能错过终止信号，导致 UI 卡在"运行中"不动。

---

#### 确认无问题的部分（不需要动）

| 模块 | 结论 |
|------|------|
| `getLanggraphApiUrl()` | 正常，基于 `platformApiBaseUrl` 正确拼接，不会回退 localhost |
| platform-api runtime_gateway | 正常，delegation token、SSE 代理、`x-project-id` 透传全部工作 |
| `createRuntimeThread()` | 正常，`buildThreadMetadata` 正确处理 graph / assistant 两种类型 |
| `@langchain/vue 1.0.29` | 版本足够，与 open-swe 的 `@langchain/react 1.0.22` 功能对等，底层共用 `@langchain/langgraph-sdk 1.9.28` |

---

#### reference_agent 的 interrupt 能力确认

reference_agent 是标准 tool-calling agent（`create_agent` + `[read_reference]` tool + middleware），**没有 interrupt 节点**。

- interrupt 场景测试需要用 `workflow_demo` graph（`apps/runtime-service/src/runtime_service/services/demo/workflow_demo/`）
- 这不影响 Phase 1-3 的开发，但 verification 阶段要用 workflow_demo 来测 interrupt 流程



### 关键改动点

---

#### A. platform-web — 核心 stream 层重写

##### A1. 修复现有 `usePlatformChatStream`（先修 Bug，再评估是否重写）
- **文件：** `apps/platform-web/src/modules/chat/composables/usePlatformChatStream.ts`（**修复**）
- **必须修复的 Bug：**
  1. **L85 `assistantId` 非响应式** — 改为 getter 函数：`assistantId: () => options.target.value?.resolvedTargetId || ''`
  2. **L27 `projectId` 静态求值** — 去掉 `const projectId = ...`，在 `scopedFetch` 内每次动态读取 `options.projectId.value.trim()`
- **策略：** 先修这两个 Bug 验证基础 chat 能跑通，再决定是原地扩展还是新建 composable

##### A2. 新增消息解析层: `stream-messages-to-ui.ts`
- **参考：** open-swe `streamMessagesToUi.ts`（完整借鉴其逻辑）
- **文件：** `apps/platform-web/src/modules/chat/stream-messages-to-ui.ts`（**新建**）
- **功能：** 
  - 将 `BaseMessage[]` + `AssembledToolCall[]`（`stream.toolCalls`）→ 平台 UI 展示的 `ChatDisplayMessage[]`
  - 识别并构建 `ToolExecutionChunk`（toolCallId、title、toolKind、status、input、output）
  - 处理流式 token 合并（`AIMessageChunk`）
  - 处理 reasoning content（`contentBlocks.type === 'reasoning'`）
  - 处理图片 content blocks

##### A3. Tool Call 可视化组件
- **参考：** open-swe `components/messages/` 目录下各类 message 渲染组件
- **文件：** `apps/platform-web/src/modules/chat/components/ChatToolCallCard.vue`（**新建**）
- **展示内容：**
  - 状态图标（spinner / check / error）
  - 工具名（人类可读格式）
  - 参数摘要（path / command 截断展示）
  - 可展开的完整 input/output
  - 耗时（elapsed ms）

##### A4. 线程状态 badge / agent status 展示
- **文件：** `apps/platform-web/src/modules/chat/components/ChatAgentStatusBar.vue`（**新建**）
- **参考：** open-swe `AgentRunCard.tsx`
- **展示内容：** running（spinner）/ interrupted（警告图标）/ error（错误图标）/ idle（最后活跃时间）

##### A5. Thread 侧边栏重写（ChatThreadDrawer → ChatThreadSidebar）
- **参考：** open-swe `AgentsSidebar.tsx`（简化版，去掉 GitHub/Slack 集成）
- **文件：** `apps/platform-web/src/modules/chat/components/ChatThreadSidebar.vue`（**新建**，替代 `ChatThreadDrawer.vue`）
- **功能：**
  - 线程列表按时间分组（今天 / 近7天 / 近30天）
  - 线程状态可视化
  - 支持搜索
  - 支持删除线程

##### A6. 主聊天页面布局重构（BaseChatTemplate）
- **参考：** open-swe `AgentThreadView.tsx` 的布局结构
- **文件：** `apps/platform-web/src/modules/chat/components/BaseChatTemplate.vue`（**重构**）
- **改动：**
  - 左侧可折叠线程侧边栏（`ChatThreadSidebar`）
  - 中部主聊天区（`ChatMessageList` + `ChatComposer` + `ChatAgentStatusBar`）
  - interrupt 时在 composer 上方浮现 `ChatInterruptPanel`

##### A7. Interrupt Panel 修复
- **文件：** `apps/platform-web/src/modules/chat/components/ChatInterruptPanel.vue`（**修复**）
- **改动：** 对齐实际 interrupt value 格式（`{value: ..., when: 'breakpoint'}`），修复 `stream.respond`/`stream.respondAll` 调用链。注意：reference_agent 无 interrupt，需用 `workflow_demo` 测试

---

#### B. platform-web — 服务层

##### B1. `workspace.service.ts` 确认无需修改
- **调研结论：** `createRuntimeThread`、`getRuntimeRunStatus`、`normalizeThread` 逻辑均正确，`getLanggraphApiUrl()` 也正确
- **备注：** 不动这个文件，把精力放在 stream composable 层

##### B2. `client.ts` 确认无需修改
- **调研结论：** `getLanggraphApiUrl()` 基于 `platformApiBaseUrl` 正确拼接，不会回退 localhost。`createLanggraphAuthorizedFetch()` 的 token 逻辑也正确
- **备注：** 不动这个文件

---

#### C. platform-api — 不需要改动

- **调研结论：** platform-api runtime_gateway 的代理层完整覆盖了 LangGraph 所有接口，delegation token 注入、SSE 透传、`x-project-id` 透传均正常
- `/threads/sidebar` 聚合接口评估：现有 `/threads/search` 完全可以满足侧边栏需求（分组逻辑在前端做），跳过这个可选增强



---

### 核心策略与决策：如何借鉴 open-swe？

针对**"当前项目的相关代码是否需要都删除，直接重写"**的问题，我们确立了以下核心战略：

**结论：坚决不能全删！采用"保留底层服务，借用 UI/解析心脏"的无痛接入策略。**

1. **绝对不能删、不能动的部分（已有的平台基础设施）：**
   - **`platform-api` / `runtime_gateway`**：处理了复杂的 Delegation Token 鉴权、网关代理、模型权限隔离。
   - **`workspace.service.ts` 和 `client.ts`**：处理了 SSE 代理、Cloudflare 拦截兜底、`x-project-id` 跨域携带。
   - **为什么？** 如果全删套 open-swe 壳，这些鉴权逻辑全得重写，必然跑不通，违背 KISS 原则。

2. **坚决借鉴（白嫖）的部分（open-swe 的精髓）：**
   - **核心解析器 `streamMessagesToUi.ts`**：剥离 open-swe 特定的 Slack/GitHub 业务逻辑后，将其原封不动地翻译为 TypeScript/Vue 适用版。它完美解决了将零碎 `BaseMessage` 组装为 `ToolExecutionChunk` 的难题。
   - **UI 渲染编排逻辑 `renderItems.ts`**：直接用于驱动新建的 `ChatToolCallCard.vue`。
   - **Stream 生命周期控制**：借鉴其对 `stream.toolCalls` 的充分利用，让 UI 实时感知工具状态。

**总结：用我们现有的"安全管道"（API 代理、鉴权），去接 open-swe 的"高级龙头"（消息解析和 UI 渲染）。**

---

### 技术选型

| 关注点 | 选型 | 理由 |
|--------|------|------|
| 流式通信 | `@langchain/vue useStream` + `stream_mode: ["messages", "events"]` | 已集成于项目，open-swe 的 React 版本与此对应 |
| 消息解析 | 借鉴 open-swe `streamMessagesToUi.ts` 逻辑，用 TS 重写为 Vue 工具函数 | open-swe 已在生产验证，成熟稳定 |
| UI 组件库 | 保持现有 tailwind + shadcn-vue 体系 | 不替换框架，降低风险 |
| 状态管理 | Vue 3 Composition API ref/computed，无需引入 Pinia | KISS 原则，open-swe 本身也是用 React hooks，同等概念 |
| thread 数据获取 | `@tanstack/query-core` via `@langchain/vue` 或直接 fetch | 对齐 open-swe 的 react-query 使用模式 |

---

### LangGraph Streaming 关键知识点（基于文档调研）

runtime-service 通过 LangGraph API Server 提供两个核心流端点，platform-api 已代理：

1. **`POST /threads/{thread_id}/runs/stream`** — 创建 run 并流式返回，`stream_mode` 支持：
   - `messages`：流式消息 token（v2 格式）
   - `events`：全量 graph 事件（on_chain_start/end, on_tool_start/end, on_llm_stream等）
   - `values`：每步完整 state

2. **`GET /threads/{thread_id}/runs/{run_id}/stream`** — 加入已有 run 的流

open-swe 使用的是 `StreamProvider`（React）= 我们的 `useStream`（Vue），底层通过 `@langchain/langgraph-sdk` Client 调用这些端点，自动处理：
- SSE 重连
- `last_event_id` 续流
- thread 懒创建（`threadId = null` 时自动创建）

---

## 链路影响

### 受影响的调用链路
```
platform-web (chat module)
  → platform-api /api/langgraph/* (runtime_gateway)
    → runtime-service (LangGraph API Server)
      → reference_agent graph
```

### 契约变更
- platform-api → platform-web：**无契约变更**，现有网关接口不动
- platform-web 内部：`usePlatformChatStream` → `useAgentThreadStream`（内部替换，不影响对外接口）

---

## 风险和依赖

- **风险1：** `@langchain/vue` 的 `useStream` API 与 open-swe 使用的 `@langchain/react` `StreamProvider` 存在差异 → **应对：** 先做小 demo 验证 `useStream` 的基本 streaming 行为，再全面重写
- **风险2：** runtime-service reference_agent 的 state schema（messages key、interrupt schema）可能与前端假设不一致 → **应对：** 先用 langgraph-cli 本地跑一次 reference_agent，观察实际 SSE 事件结构
- **风险3：** platform-api delegation token 过期或 scope 不匹配导致流被 401 → **应对：** 不动 gateway 鉴权逻辑，只修前端

---

## 实施计划

1. **Phase 1（第 1-3 天）：调研验证 + 基础修复**
   - 本地运行 runtime-service，用 curl 验证 SSE 流的实际事件格式
   - 修复 langgraph client URL 配置
   - 修复 `workspace.service.ts` 中 `createRuntimeThread` 和 `getRuntimeRunStatus`
   - 验证基础 chat 能发消息、能收到流式回复

2. **Phase 2（第 4-7 天）：stream 层重写 + 消息解析**
   - 实现新 `useAgentThreadStream` composable
   - 借鉴 open-swe `streamMessagesToUi.ts` 实现平台版消息解析
   - 实现 `ChatToolCallCard.vue` 工具调用可视化
   - 重写 `ChatMessageList.vue` 消费新的消息格式

3. **Phase 3（第 8-11 天）：UI 重构 + agent 生命周期展示**
   - 重写 `BaseChatTemplate.vue` 布局（三栏布局）
   - 实现 `ChatThreadSidebar.vue`（线程列表侧边栏）
   - 实现 agent status indicator（running/interrupted/error 状态展示）
   - 修复 `ChatInterruptPanel.vue`

4. **Phase 4（第 12-14 天）：端到端测试 + 收尾**
   - 完整链路测试（发消息 → 流式回复 → tool call 展示 → interrupt 确认 → 完成）
   - 单元测试更新
   - 文档更新
