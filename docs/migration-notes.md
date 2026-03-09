# 迁移说明

## 1. 当前阶段完成项

- 已创建 `main` 备份分支
- 已创建新的整合工作分支
- 已创建 `apps/*` 目录骨架
- 已将旧版 `AITestLab` 代码归档到 `archive/legacy-aitestlab/root/`
- 已将四部分代码迁入 `apps/*`
- 已验证 `runtime-service` 在新目录下可启动
- 已验证 `platform-api` 在新目录下可启动，并可联调 `runtime-service`

## 2. 当前阶段未做的事

- 未统一 Python 依赖
- 未统一 Node 依赖
- 未改业务代码路径
- 未改现有服务的核心运行逻辑
- 未统一根级 `.pre-commit-config.yaml`

## 3. 当前验证结论

### 3.1 已通过

- `apps/runtime-service`
  - `/info` 返回 `200`
  - `/internal/capabilities/models` 返回 `200`
  - `/internal/capabilities/tools` 返回 `200`
- `apps/platform-api`
  - 已成功连接本地 PostgreSQL
  - 已成功调用 `apps/runtime-service`
  - `/api/langgraph/info` 返回 `200`
  - `/_management/catalog/models/refresh` 返回 `200`
  - `/_management/catalog/tools/refresh` 返回 `200`

### 3.2 当前阻塞项

- `apps/platform-web`
  - `pnpm build` 失败
  - 原因：`next/font` 拉取 `IBM Plex Sans` 时外网超时
- `apps/runtime-web`
  - `pnpm build` 失败
  - 原因：`next/font` 拉取 `Inter` 时外网超时

这两项属于外部字体资源下载问题，不是当前仓库结构迁移导致的代码错误。

## 4. 已知后续事项

- 补根级统一脚本
- 逐步清理根级 README 历史内容
- 统一工具链到 `uv + Python 3.13`
- 评估是否需要共享包/公共类型层

## 5. 当前建议

- 先按应用目录分别启动和验证
- 每迁入一块，就做最小运行检查
- 不在迁移早期叠加“目录重组 + 依赖重组 + 架构重写”三件事
