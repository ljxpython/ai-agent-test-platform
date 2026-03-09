# 代码架构说明（当前实现）

## 1. 总览

当前系统由两部分组成：

- 后端：FastAPI（管理接口 + 运行时透传）
- 前端：Next.js（管理界面 + 聊天界面）

核心方向：

- 管理能力统一走 `/_management/*`
- 运行时能力通过 `/_runtime/*` 与透传入口接入 LangGraph

## 2. 后端架构

### 2.1 应用装配入口

- `main.py`：仅负责 `app = create_app()`
- `app/factory.py`：应用真实装配入口

`app/factory.py` 当前装配内容：

1. 挂载路由
   - `management_router`（`/_management/*`）
   - `langgraph_router`
   - `frontend_passthrough_router`
2. 注册中间件
   - auth context
   - audit log
   - request context
3. 透传路由
   - `/_runtime/{full_path:path}`
   - `/{full_path:path}`（兼容透传）

### 2.2 管理接口分层

目录：`app/api/management/`

主要模块：

- `auth.py`：登录/刷新/登出/改密
- `users.py`：用户 CRUD、`/users/me`
- `projects.py`：项目管理
- `members.py`：项目成员管理
- `audit.py`：审计查询
- `common.py`：通用鉴权/上下文工具

### 2.3 数据层

目录：`app/db/`

- `models.py`：`users/projects/project_members/refresh_tokens/audit_logs` 等模型
- `access.py`：数据访问函数（查询、写入、约束）
- `session.py`：会话与事务封装
- `init_db.py`：初始化核心表

## 3. 前端架构

### 3.1 主体目录

- `agent-chat-ui/src/app/workspace/*`：管理台页面
- `agent-chat-ui/src/lib/management-api/*`：管理接口客户端
- `agent-chat-ui/src/components/platform/*`：管理台组件（分页、搜索、确认弹窗、列拖拽）

### 3.2 管理页面

- `workspace/projects`
- `workspace/projects/[projectId]/members`
- `workspace/users`
- `workspace/users/[userId]`
- `workspace/audit`
- `workspace/me`

### 3.3 通用交互能力

- 统一分页组件（支持页大小与指定页跳转）
- 统一搜索组件
- 统一危险操作确认弹窗
- 表格列宽拖拽（含双击重置）

## 4. 请求链路

### 4.1 管理接口链路

前端页面 -> `management-api client` -> `/_management/*` -> DB

### 4.2 运行时链路

前端/调用方 -> `/_runtime/*`（或兼容透传）-> LangGraph 上游

## 5. 当前权威文档

优先参考：

1. `docs/management-console-overview.md`
2. `docs/self-hosted-auth-rbac-mvp.md`
3. `docs/testing.md`

历史方案与旧架构文档统一放在 `docs/archive/`。
