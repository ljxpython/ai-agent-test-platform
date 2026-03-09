# 仓库结构说明

## 1. 总体结构

本仓库采用 `apps/*` 的方式组织四个独立运行单元：

- `apps/platform-api`
- `apps/platform-web`
- `apps/runtime-service`
- `apps/runtime-web`

根目录仅保留公共层：

- `docs/`
- `scripts/`
- `archive/`

## 2. 四个应用的职责

### 2.1 `apps/platform-api`

- 平台控制面后端
- 提供：
  - `/_management/*`
  - `/api/langgraph/*`
  - 平台数据库能力
  - 鉴权与审计

### 2.2 `apps/platform-web`

- 平台主前端
- 面向：
  - 管理台
  - 平台侧聊天 UI
  - assistant / graphs / runtime catalog 页面

### 2.3 `apps/runtime-service`

- LangGraph 执行层
- 核心内容在 `graph_src_v2`
- 负责：
  - 图执行
  - 模型装配
  - 工具 / MCP 装配
  - runtime 自定义能力路由

### 2.4 `apps/runtime-web`

- 直连 runtime 的调试前端
- 用于独立验证 LangGraph server 本身
- 不经过平台 API

## 3. 文档放置规则

- 每个应用自己的 `docs/`：只放该应用内部开发文档
- 根目录 `docs/`：只放全局文档

## 4. 后续演进原则

- 第一阶段：目录重组 + 运行验证
- 第二阶段：再考虑根级工具链统一、脚本统一、文档清理
- 第三阶段：按需要再评估共享包/公共类型/公共脚本
