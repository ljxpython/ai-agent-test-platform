# AITestLab

## 1. 当前定位

本仓库正在从旧版 `AITestLab` 逐步迁移到新的四段式结构：

- `apps/platform-api`：平台后端（FastAPI + PostgreSQL + 管理接口）
- `apps/platform-web`：平台前端（Next.js，走平台后端）
- `apps/runtime-service`：LangGraph 执行层（`graph_src_v2`）
- `apps/runtime-web`：LangGraph 直连调试前端

当前阶段目标：

- 先完成仓库重组
- 保持四部分代码仍可独立运行
- 暂不进行依赖融合与代码层重构

## 2. 目录结构

```text
AITestLab/
├── apps/
│   ├── platform-api/
│   ├── platform-web/
│   ├── runtime-service/
│   └── runtime-web/
├── docs/
├── scripts/
└── archive/
```

详细说明见：

- `docs/repo-layout.md`
- `docs/local-dev.md`
- `docs/env-matrix.md`
- `docs/migration-notes.md`
- `docs/planning/apps-split-migration-plan.md`

## 3. 当前约定

- 每个应用独立维护自己的环境与依赖
- 每个应用内部 `docs/` 保留自己的开发文档
- 根目录 `docs/` 只放全局说明、联调说明、迁移规划与公共约定

## 4. 本地开发入口

常用脚本：

- `scripts/dev-up.sh`
- `scripts/dev-down.sh`
- `scripts/check-health.sh`

更详细的本地联调说明见 `docs/local-dev.md`。

## 5. 旧代码说明

旧版 `AITestLab` 代码已整体归档到：

- `archive/legacy-aitestlab/root/`

当前根目录不再直接承载旧版业务代码。
