# 实现状态栏与侧边栏 (Phase 3)

## 改动时间
2026-09-08

## 相关任务
- Task 3.1: 实现 `ChatAgentStatusBar.vue`
- Task 3.2: 实现 `ChatThreadSidebar.vue`

## 改动文件
- `apps/platform-web/src/modules/chat/components/ChatAgentStatusBar.vue` (新建)
- `apps/platform-web/src/modules/chat/components/ChatThreadSidebar.vue` (新建)
- `apps/platform-web/src/modules/chat/components/BaseChatTemplate.vue` (修改)
- `apps/platform-web/src/modules/chat/components/ChatThreadDrawer.vue` (待删除/已解绑)

## 具体改动

### 1. `ChatAgentStatusBar.vue` (Task 3.1)
- 作为常驻的顶部状态指示器插入到了 `ChatMessageList` 上方（吸顶显示 `sticky top-0`）。
- 接收 `isRunning`, `isInterrupted`, `error`, `lastEventAt`，在 Agent 运行时给用户直接的进度反馈（代替之前散落在页面各处的零碎信息）。

### 2. `ChatThreadSidebar.vue` (Task 3.2)
- 废弃了原有的 `ChatThreadDrawer`（抽屉式的会话列表体验较差）。
- 复用了 `thread-list-view-model.ts` 中的分组逻辑，在左侧建立了一个固定的 Sidebar，支持**今天、昨天、最近一周**等时间维度分组。
- 支持直接在侧边栏内搜索过滤、切换状态，以及点击新建会话。

### 3. `BaseChatTemplate.vue` 布局升级
- 将原有的 `SurfaceCard` 包裹了一层 `flex flex-1 gap-4`，使 `ChatThreadSidebar` 和主聊天区左右并排。
- 移除了原有的 "会话(n)" 打开 Drawer 的按钮，减少了用户的点击层级。

## 影响
- **UI：** 页面从单面板变成了类似于 open-swe 的**双面板**（侧边栏 + 主对话）。
- **可用性：** 历史会话随手可及，Agent 执行状态一目了然。

## 验证
- [x] 代码静态检查通过
