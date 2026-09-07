# Docs 文档导航

目标：让人和 AI 只读取当前任务需要的最小文档集合。

## 1. 开始一个任务

1. [根目录 AGENTS.md](../AGENTS.md) —— 开发流程、改动分级标准（本地/链路/治理改动）、Skills 入口
2. 最窄的 app/service 自己的 `docs/`（如 `apps/platform-api/docs/`）

不要默认读取整个 `docs/` 目录。

## 2. 启动、部署和运维

- [本地开发说明](./quickstart/local-dev.md)
- [环境变量矩阵](./quickstart/env-matrix.md)
- [部署文档](./quickstart/deployment-guide.md)
- [本地部署契约](./local-deployment-contract.yaml)
- [容器化交付指南](../deploy/README.md)
- [从零到一容器化部署](./quickstart/zero-to-one-container-deploy.md)
- [容器更新 Runbook](./runbooks/container-update-runbook.md)

## 3. 变更与发布

- [提交与 Changelog 规范](./guides/commit-and-changelog-guidelines.md)
- [更新日志](./CHANGELOG.md)
- [发布记录](./releases/)

链路/治理改动的项目文档统一放在 [projects/](./projects/) 下，使用 `/plan-project` Skill 创建。

## 4. 目录说明

- `quickstart/`：新人必读（架构、本地开发、部署）
- `guides/`：开发规范
- `projects/`：链路/治理改动的项目文档
- `decisions/`：技术决策（ADR）
- `archive/`：过时内容归档
- `releases/`：历史发布记录
- `runbooks/`：运维操作手册
