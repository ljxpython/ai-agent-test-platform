# 文档索引

## 文档清单

- `docs/management-console-overview.md`：管理界面功能总览（Project/User/Audit/My Profile）。
- `docs/dev-tunnel-guide.md`：SSH 开发隧道教学文档（`scripts/dev_tunnel_up.sh` / `scripts/dev_tunnel_down.sh` 的用途、用法与排障）。
- `docs/langgraph-passthrough-guide.md`：LangGraph 同构入参与出参透传教学文档（`app/api/langgraph`、前端兼容透传、底层 runtime 透传的关系与实现）。
- `docs/chat-file-upload-guide.md`：Chat 页面图片 / PDF 上传链路教学文档（前端编码、多模态消息结构、平台层接收数据、扩展更多类型时的改造点）。
- `docs/postgres-operations.md`：PostgreSQL 容器启动、停止、备份与迁移手册。
- `docs/code-architecture.md`：当前与目标代码架构设计。
- `docs/assistant-management-design.md`：Assistant 管理页面与前后端接口落地方案。
- `docs/runtime-object-catalog-design.md`：Graph / Assistant / Model / Tool 四类对象的平台库表结构与同步策略设计。
- `docs/self-hosted-auth-rbac-mvp.md`：自建认证与权限系统 MVP 决策稿（去 Keycloak/OpenFGA）。
- `docs/error-playbook.md`：已遇到问题与修复手册（防踩坑）。
- `docs/testing.md`：自动化冒烟测试脚本与运行方式。
- `docs/logging-system.md`：前后端日志系统说明（落盘路径、关键埋点、验证步骤）。
- `docs/ci-troubleshooting.md`：CI 失败诊断与本地复现指引。

## 已归档文档（docs/archive）

- `docs/archive/keycloak-integration.md`
- `docs/archive/openfga-integration.md`
- `docs/archive/platform-api.md`
- `docs/archive/server-migration-guide.md`
- `docs/archive/execution-status.md`
- `docs/archive/frontend-platform-plan.md`
- `docs/archive/auth-tenant-project-flow.md`
- `docs/archive/platform-plan.md`
- `docs/archive/assistant-greenfield-design.md`
- `docs/archive/fastapi-service-architecture.md`
- `docs/archive/langgraph-official-usage.md`

## 文档约定

- 从现在开始，`docs/` 下文档统一使用中文描述。
- 命令示例优先可直接复制执行，避免抽象说明。
