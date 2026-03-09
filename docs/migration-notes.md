# 迁移说明

## 1. 当前阶段完成项

- 已创建 `main` 备份分支
- 已创建新的整合工作分支
- 已创建 `apps/*` 目录骨架
- 旧版 `AITestLab` 代码已从当前工作分支移除，并由远端备份分支保存
- 已将四部分代码迁入 `apps/*`
- 已验证 `runtime-service` 在新目录下可启动
- 已验证 `platform-api` 在新目录下可启动，并可联调 `runtime-service`
- 已验证 `platform-web` 可构建
- 已验证 `runtime-web` 可构建

## 2. 当前阶段未做的事

- 未统一 Python 依赖
- 未统一 Node 依赖
- 未改业务代码路径
- 未改现有服务的核心运行逻辑
- 根级 `.pre-commit-config.yaml` 当前已临时禁用，后续再按 `uv + Python 3.13` 统一启用

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

- 当前阶段未发现新的结构性阻塞项
- `platform-web` / `runtime-web` 已移除对 Google Fonts 构建时出网依赖
- 当前仍可能存在少量 lint warning，但不影响构建与运行验证结论

## 4. 已知后续事项

- 补根级统一脚本
- 逐步清理根级 README 历史内容
- 统一工具链到 `uv + Python 3.13`
- 重新设计并启用根级 `.pre-commit-config.yaml`
- 评估是否需要共享包/公共类型层

## 5. 当前建议

- 先按应用目录分别启动和验证
- 每迁入一块，就做最小运行检查
- 不在迁移早期叠加“目录重组 + 依赖重组 + 架构重写”三件事
