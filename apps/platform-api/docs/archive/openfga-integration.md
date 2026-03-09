# OpenFGA 集成说明

## 作用

OpenFGA 用于资源级授权，把“谁可以对哪个 tenant/project/agent 做什么操作”从代码里抽离出来。

## 本地启动

```bash
docker rm -f agent-openfga 2>/dev/null || true
docker run -d \
  --name agent-openfga \
  -p 18081:8080 \
  openfga/openfga:latest \
  run
```

## 初始化 store 和 model

```bash
PYTHONPATH=. OPENFGA_URL=http://127.0.0.1:18081 uv run python scripts/setup_openfga.py
```

输出示例：

```text
OPENFGA_STORE_ID=01J...
OPENFGA_MODEL_ID=01J...
```

把这两个值写入 `.env`。

## `.env` 配置

```env
OPENFGA_ENABLED=true
OPENFGA_AUTHZ_ENABLED=true
OPENFGA_AUTO_BOOTSTRAP=false
OPENFGA_URL=http://127.0.0.1:18081
OPENFGA_STORE_ID=<store-id>
OPENFGA_MODEL_ID=<model-id>
OPENFGA_MODEL_FILE=config/openfga-models/v1.json
```

## 开发环境与生产环境访问约定

- 开发环境（推荐）：服务器仅开放 `22`，通过 SSH 隧道访问 OpenFGA。
- 开发环境示例：`OPENFGA_URL=http://127.0.0.1:18081`（本机转发端口）。
- 生产环境建议：OpenFGA 放在私有网络，`OPENFGA_URL` 使用内网地址；如必须对外访问，只通过受控入口暴露。
- 详细网络边界与端口策略见：`docs/server-migration-guide.md`。

## 已接入逻辑

- 创建租户/成员变更时，同步 tenant 角色 tuple（`owner/admin/member`）。
- 删除成员时，回收 tenant 角色 tuple。
- 创建项目时，同步 `project -> tenant` 关系。
- 删除项目时，回收 `project -> tenant` 关系及其下 agent 关系。
- 创建智能体时，同步 `agent -> project` 关系。
- 删除智能体时，回收 `agent -> project` 关系。
- 透传请求在带 `x-tenant-id` 时，按方法映射 `can_read/can_write` 做 `check`。
- 透传请求带 `x-agent-id` 时，增加 `agent` 级别 `check` 与 agent-tenant 映射一致性校验。

## 联调验证

1. 使用 owner 用户创建 tenant/project/agent。
2. 使用 member 用户调用读接口应通过。
3. member 写透传请求在策略开启时应被 `403` 拦截。

## 模型版本管理与迁移

模型文件目录：`config/openfga-models/`

当前默认版本：`config/openfga-models/v1.json`

当需要升级模型：

1. 新增版本文件（例如 `config/openfga-models/v2.json`）
2. 执行迁移脚本写入新模型：

```bash
PYTHONPATH=. OPENFGA_URL=http://127.0.0.1:18081 \
OPENFGA_STORE_ID=<store-id> \
OPENFGA_MODEL_FILE=config/openfga-models/v2.json \
uv run python scripts/openfga_model_migrate.py --apply
```

3. 把输出的 `OPENFGA_MODEL_ID` 与 `OPENFGA_MODEL_FILE` 更新到 `.env`
4. 重启服务并运行 `scripts/smoke_e2e.py` 验证

## 模型回滚脚本（Step 2）

当新模型上线后需要回滚到历史 `model_id`：

```bash
PYTHONPATH=. OPENFGA_URL=http://127.0.0.1:18081 \
OPENFGA_STORE_ID=<store-id> \
uv run python scripts/openfga_model_rollback.py \
  --model-id <target_model_id> \
  --env-file .env \
  --apply
```

行为说明：

- 先验证目标 `model_id` 在 OpenFGA store 中存在
- 再把 `.env` 的 `OPENFGA_MODEL_ID` 更新为目标值
- 回滚后重启服务并执行 `scripts/smoke_e2e.py`

## 服务器迁移参考

如果要把本地 OpenFGA/Keycloak/PG 一起迁移到服务器，请直接参考：

- `docs/server-migration-guide.md`
