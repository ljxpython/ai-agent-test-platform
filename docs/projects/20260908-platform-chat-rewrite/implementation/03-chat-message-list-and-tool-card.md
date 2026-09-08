# 实现 Tool Call 卡片与更新消息列表重构

## 改动时间
2026-09-08

## 相关任务
- Task 2.4: 新增 `ChatToolCallCard.vue`
- Task 2.5: 更新 `ChatMessageList.vue` 使用新消息格式

## 改动文件
- `apps/platform-web/src/modules/chat/components/ChatToolCallCard.vue` (新建)
- `apps/platform-web/src/modules/chat/components/ChatMessageList.vue` (重写)
- `apps/platform-web/src/modules/chat/components/BaseChatTemplate.vue` (更新)

## 具体改动

### 1. `ChatToolCallCard.vue` (Task 2.4)
- 支持传入 `ToolExecutionChunk`，以折叠面板展示 Tool Call 的输入输出。
- 利用 `chunk.status` (pending, in_progress, completed, error) 控制图标及颜色。
- 保证参数及日志大段文本展示时自动包裹、带滚动条，且容错处理 JSON 解析。

### 2. `ChatMessageList.vue` 重构 (Task 2.5)
- **Props 更换：** 将原先的 `displayMessages` (legacy) 替换为了 `AgentDisplayMessage[]` (由 `streamMessagesToUi` 产出)。
- **渲染逻辑扁平化：**
  - 不再通过 `ChatMessageMeta` 单独挂载执行状态，而是直接通过 `v-for="chunk in displayEntry.chunks"` 依次渲染文本（Markdown）、思考过程（Reasoning）、以及工具卡片（ChatToolCallCard）。
  - 支持 `imageChunks` 显示上传的图片。
- **操作向后兼容：**
  - 原来遗留的 edit / branch / retry 逻辑高度绑定 `Message` (LangGraph) 对象。
  - 我们通过 `getOriginalMessage(displayEntry.id)` 来根据 `AgentTurn` 获取到底层对应的初始消息，从而让原有的 branch 等高级能力继续工作！

### 3. 接入 `BaseChatTemplate.vue`
- 更新其向下传递 `:display-messages="workspace.uiMessages.value"`。

## 影响
- **UI：** 页面焕然一新，对齐了 open-swe 方案，去掉了原来通过 `ChatMessageMeta` 强行包裹 tool-calls 的结构。现在的消息流更符合"Chunk流式拼装"理念。
- **安全性：** 旧的 `messages` 依然存在（Task 2.3 已验证），底层功能不受影响。

## 验证
- [x] 代码编译就绪
- [ ] 待后续前台验证真实流
