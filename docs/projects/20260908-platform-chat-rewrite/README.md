# platform-chat-rewrite

## 项目概述
- **时间：** 2026-09-08 至 预计 2026-09-22（约 2 周）
- **目标：** 完全重写平台层（platform-web + platform-api）对话功能，借鉴 open-swe 的 agent 交互体验，实现与 runtime-service（LangGraph API Server）的高质量 SSE 流式通信，前端展示完整 agent 生命周期活动
- **负责人：** @lijiaxin
- **状态：** Phase 3 完成

## 快速导航
- [整体方案](plan.md)
- [任务拆分](tasks.md)
- [验证计划](verification.md)

## 改动范围
- **影响服务：** platform-web、platform-api（runtime_gateway）、runtime-service（无需改动，但需对齐其 API 行为）
- **改动级别：** 链路改动
- **预计工作量：** 10～14 人天

## 关键决策
1. **前端框架保持 Vue 3，不迁移 React**：借鉴 open-swe 的架构思路和 UI 组件设计，但用 Vue 3 Composition API + `@langchain/vue` 的 `useStream` 重新实现，避免改技术栈
2. **流式通信协议用 LangGraph stream_mode=events（v2 格式）**：open-swe 通过 `@langchain/react` `StreamProvider` + `useStreamContext` 消费 LangGraph 标准 SSE 流；我们项目已有 `useStream`（`@langchain/vue`），但当前实现存在问题，需要彻底重写 stream 层
3. **platform-api runtime_gateway 不需要改接口契约**：现有网关接口已经代理了 LangGraph 所有接口（threads、runs/stream、runs/stream events），前端直接打过去就行，后端不动
4. **UI 目标：类 open-swe AgentThreadView 体验**：线程列表（侧边栏）+ thread 详情页 + 实时 agent 活动时间线（tool call 可视化）+ interrupt 确认面板
