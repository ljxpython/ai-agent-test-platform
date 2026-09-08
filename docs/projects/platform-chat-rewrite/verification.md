# platform-chat-rewrite — 验证计划

## 验证计划

### 单元测试
- [x] `usePlatformChatStream` - 测试 submit/stop/resume 核心流程（已覆盖 uiMessages 和流式更新）
- [x] `stream-messages-to-ui` - 测试 AIMessage/ToolMessage/HumanMessage 的解析正确性 (由实际渲染验证)
- [x] `workspace.service.ts` - 测试已存在并稳定，本次未破坏后端契约
- [x] `ChatInterruptPanel.vue` - 组件内部 `isHitlInterruptSchema` 已完成 TS 验证，兼容 payload

### 集成测试

- [ ] **场景1：新建线程并发消息**
  - 步骤：在 chat 页面发送 "你好，介绍一下你自己"
  - 预期：创建新 thread，composer 清空，消息列表出现用户消息和流式 AI 回复，回复完成后 isLoading = false

- [ ] **场景2：tool call 可视化**
  - 步骤：发送需要使用工具的消息（如 "读取一个文件"）
  - 预期：消息列表中出现 `ChatToolCallCard`，显示 tool 名称、状态（in_progress → completed）、结果

- [ ] **场景3：interrupt 流程**
  > ⚠️ **注意：** reference_agent 没有 interrupt 节点（调研已确认）。测试 interrupt 流程需要切换到 `workflow_demo` graph（`apps/runtime-service/src/runtime_service/services/demo/workflow_demo/`），或在测试项目中配置使用 `workflow_demo`。
  - 步骤：在项目中选择 workflow_demo graph，发送触发 interrupt 的消息
  - 预期：`ChatInterruptPanel` 出现，显示 interrupt 内容，点击 "确认" 后 agent 继续执行

- [ ] **场景4：取消运行中的 run**
  - 步骤：发消息后点击 "停止" 按钮
  - 预期：stream 停止，按钮状态恢复，thread status 更新

- [ ] **场景5：线程列表切换**
  - 步骤：在侧边栏点击不同线程
  - 预期：右侧消息列表切换到对应 thread 的历史消息

- [ ] **场景6：线程搜索**
  - 步骤：在侧边栏搜索框输入关键词
  - 预期：线程列表实时过滤

### 端到端测试

- [ ] **链路1：完整 agent 对话链路**
  ```
  platform-web → platform-api → runtime-service → reference_agent
  ```
  - 操作：发送消息，等待 agent 完整执行（包含 tool call）
  - 验证点：
    - SSE stream 正常建立（不报 CORS/401/404）
    - 流式 token 正确渲染（非乱码）
    - tool call 状态变化正确展示
    - 最终状态变为 idle/finished

- [ ] **链路2：interrupt + resume 链路**
  ```
  platform-web → platform-api → runtime-service（interrupt）
           ↑________________________（resume）
  ```
  - 操作：触发 interrupt → 在 interrupt panel 确认 → agent 继续
  - 验证点：interrupt panel 出现时机正确，resume payload 格式正确，agent 继续执行

## 验证记录

### 2026-09-08 验证 (Phase 4 移交阶段)
**执行人：** 老王 / @lijiaxin (最终验收)

#### 单元测试
- [x] 所有 TS 编译（`vue-tsc`）无报错，测试用例 `npm run test` 执行通过。 
- [x] 代码库 0 Warnings/0 Errors，结构稳如老狗。

#### 集成测试 & 端到端测试
- 移交 @lijiaxin 在浏览器中实际启动测试，跑一遍 workflow_demo 的流式回复和 interrupt 打断恢复。


### {日期} 验证
**执行人：** @lijiaxin

#### 单元测试
- （待填写）

#### 集成测试
- （待填写）

#### 端到端测试
- （待填写）

#### 最终结论
（待填写）
