# 实现消息解析层 (stream-messages-to-ui.ts)

## 改动时间
2026-09-08

## 相关任务
- Task 2.2: 实现消息解析层 `streamMessagesToUi.ts`

## 改动文件
- `apps/platform-web/src/modules/chat/agent-types.ts` (新建)
- `apps/platform-web/src/modules/chat/stream-messages-to-ui.ts` (新建)

## 具体改动

### 1. 新建 `agent-types.ts`
引入了 open-swe 里的 Chunk 范式（TextChunk, ToolExecutionChunk, ReasoningChunk, ImageChunk 等）。
**理由：** 让前端 UI 组件能以"块"为单位渲染消息，而不再被死板的 legacy Message 格式局限，极大增强扩展性。

### 2. 移植 `streamMessagesToUi.ts`
把 `BaseMessage[]` 和 `AssembledToolCall[]` 作为输入，聚合出 `ChatDisplayMessage[]`。
核心突破点：
- **状态同步：** `AssembledToolCall` 直接映射为 UI 上的 Tool 卡片状态。不再需要 `pendingTools` 手动管理。
- **Reasoning 处理：** 支持解析大模型的 `reasoning` block。
- **差异识别：** 提供 `toolKind` 供前端渲染判断，对编辑文件等特殊 tool 直接转为 diff 数据（`maybeDiffFromArgs`）。

## 影响
- ✅ 纯新增解析逻辑，暂未替换现有展示层，非常安全。

## 验证
- [x] 代码已就绪，无类型报错。
