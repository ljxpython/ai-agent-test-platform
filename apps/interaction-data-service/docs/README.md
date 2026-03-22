# 文档导航

`apps/interaction-data-service` 当前已经有真实代码，但不同文档承担的职责不同：

- `README.md` / `docs/README.md`：帮助你快速定位当前代码、表和接口
- `docs/usecase-workflow-design.md`：定义用例工作流的目标设计与后续收敛方向
- `docs/service-design.md`：描述更高层的服务边界和通用契约

当前与 `usecase_workflow_agent` 相关的阅读顺序建议是：

1. `apps/runtime-service/graph_src_v2/services/usecase_workflow_agent/README.md`
2. `apps/runtime-service/graph_src_v2/services/usecase_workflow_agent/refactor-plan.md`
3. `docs/usecase-workflow-design.md`
4. 本文（用于查表、查接口、排查数据）

需要特别说明：

- 当前代码里仍然存在 workflow / snapshot / review 相关接口与表
- 但下一轮优化的推荐主路径，将优先保留：
  - 附件解析产物
  - 最终正式用例
- 也就是优先围绕：
  - `/api/usecase-generation/workflows/documents`
  - `/api/usecase-generation/use-cases`

因此本文里关于 workflow/snapshot 的内容，更多用于“排查当前代码”和“识别清理候选”，不代表这些接口会继续作为长期推荐主路径。

## 当前代码里怎么查解析结果和用例数据

如果你现在要确认 PDF、图片或其他源文档解析结果到底有没有写进 `interaction-data-service`，先记住下面几件事。

### 1. 先确认数据库连的是哪一个实例

数据库连接不是写死的，代码从环境变量读取：

- `app/config.py` 里的 `load_settings()` 读取 `DATABASE_URL`
- `INTERACTION_DB_ENABLED=true` 时才会真的启用数据库
- `INTERACTION_DB_AUTO_CREATE=true` 时服务启动会自动建表
- `app/db/session.py` 明确要求，启用数据库时 `DATABASE_URL` 不能为空

建议先在本地服务目录确认当前环境值：

```bash
cd apps/interaction-data-service
python - <<'PY'
from dotenv import load_dotenv
from app.config import load_settings

load_dotenv()
settings = load_settings()
print("INTERACTION_DB_ENABLED=", settings.interaction_db_enabled)
print("INTERACTION_DB_AUTO_CREATE=", settings.interaction_db_auto_create)
print("DATABASE_URL=", settings.database_url)
PY
```

如果你只想快速看 `.env` 里有没有配，也可以直接执行：

```bash
cd apps/interaction-data-service
rg "^(DATABASE_URL|INTERACTION_DB_ENABLED|INTERACTION_DB_AUTO_CREATE)=" .env .env.*
```

`DATABASE_URL` 可能指向 PostgreSQL，也可能指向 SQLite 或别的 SQLAlchemy 支持的后端。排查时先看真实配置，再决定用什么客户端，不要在文档里假设数据库类型。

### 2. 哪些表存 parsed documents 和 use cases

当前代码里的主要表定义在 `app/db/models.py`。

- `requirement_documents`
  - 存上传后的源文档和解析产物
  - PDF 或图片解析结果重点看这些列
    - `summary_for_model`
    - `parsed_text`
    - `structured_data`
    - `provenance`
    - `confidence`
    - `error`
- `usecase_workflows`
  - 存一次用例生成工作流主记录
- `usecase_workflow_snapshots`
  - 存每轮候选用例快照，主要内容在 `payload_json`
- `usecase_review_reports`
  - 存评审报告，主要内容在 `payload_json`
- `use_cases`
  - 存最终正式用例，主要内容在 `content_json`

如果你要回答“解析后的 PDF 或图片结果在哪”，首选查 `requirement_documents`。如果你要回答“最终落库的用例在哪”，查 `use_cases`。

### 3. 本地直接连库怎么查

先从 `DATABASE_URL` 判断你该用什么客户端。

#### PostgreSQL 例子

如果 `DATABASE_URL` 形如 `postgresql+psycopg://user:pass@host:5432/dbname`，本地可以先转成 `psql` 可直接使用的 URL：

```bash
cd apps/interaction-data-service
python - <<'PY'
from dotenv import load_dotenv
from app.config import load_settings

load_dotenv()
url = load_settings().database_url or ""
print(url.replace("postgresql+psycopg://", "postgresql://", 1))
PY
```

然后连接数据库：

```bash
psql "postgresql://user:pass@host:5432/dbname"
```

#### SQLite 例子

如果 `DATABASE_URL` 形如 `sqlite:///./interaction_data.db`，可以直接用：

```bash
cd apps/interaction-data-service
sqlite3 interaction_data.db
```

### 4. 直接查 parsed source documents 的 SQL 示例

先看最近写入的文档和解析状态：

```sql
select
  id,
  project_id,
  workflow_id,
  filename,
  content_type,
  source_kind,
  parse_status,
  confidence,
  created_at
from requirement_documents
order by created_at desc
limit 20;
```

重点检查 PDF 或图片解析字段：

```sql
select
  id,
  filename,
  parse_status,
  summary_for_model,
  parsed_text,
  structured_data,
  provenance,
  confidence,
  error
from requirement_documents
where id = '<document_id>';
```

如果你只想找解析失败的数据：

```sql
select
  id,
  filename,
  parse_status,
  error,
  created_at
from requirement_documents
where error is not null
order by created_at desc;
```

### 5. 直接查工作流和最终用例的 SQL 示例

查看工作流主记录：

```sql
select
  id,
  project_id,
  requirement_document_id,
  title,
  status,
  latest_snapshot_id,
  persistable,
  created_at,
  updated_at
from usecase_workflows
order by updated_at desc
limit 20;
```

查看某个工作流的候选快照：

```sql
select
  id,
  workflow_id,
  version,
  status,
  review_summary,
  deficiency_count,
  payload_json,
  created_at
from usecase_workflow_snapshots
where workflow_id = '<workflow_id>'
order by version desc;
```

查看最终正式用例：

```sql
select
  id,
  project_id,
  workflow_id,
  snapshot_id,
  title,
  status,
  content_json,
  created_at,
  updated_at
from use_cases
order by updated_at desc
limit 20;
```

### 6. 不进数据库，直接走 HTTP 怎么查

当前接口前缀来自：

- `app/api/__init__.py` -> `/api`
- `app/api/usecase_generation/__init__.py` -> `/api/usecase-generation`

所以你应该使用下面这些真实路径。

这里的 `<interaction-data-service-base-url>` 故意不写死端口：这个服务目前不在根级默认四应用联调集合里，排查时应以你实际启动的地址为准。

#### 6.1 查 parsed documents

- `GET /api/usecase-generation/workflows/documents`
- `GET /api/usecase-generation/workflows/documents/{document_id}`

示例：

```bash
curl "<interaction-data-service-base-url>/api/usecase-generation/workflows/documents?project_id=<project_id>&limit=20"
```

```bash
curl "<interaction-data-service-base-url>/api/usecase-generation/workflows/documents/<document_id>"
```

返回体里就会直接包含这些解析字段：

- `summary_for_model`
- `parsed_text`
- `structured_data`
- `provenance`
- `confidence`
- `error`

#### 6.2 查工作流和候选快照

- `GET /api/usecase-generation/workflows`
- `GET /api/usecase-generation/workflows/{workflow_id}`
- `GET /api/usecase-generation/workflows/{workflow_id}/snapshots`

示例：

```bash
curl "<interaction-data-service-base-url>/api/usecase-generation/workflows?project_id=<project_id>&limit=20"
```

```bash
curl "<interaction-data-service-base-url>/api/usecase-generation/workflows/<workflow_id>/snapshots"
```

#### 6.3 查最终 use cases

- `GET /api/usecase-generation/use-cases`
- `GET /api/usecase-generation/use-cases/{use_case_id}`

示例：

```bash
curl "<interaction-data-service-base-url>/api/usecase-generation/use-cases?project_id=<project_id>&limit=20"
```

```bash
curl "<interaction-data-service-base-url>/api/usecase-generation/use-cases/<use_case_id>"
```

### 7. 一个最快的排查顺序

如果你只是要快速回答“数据到底有没有落进去”，推荐按这个顺序查：

1. 看 `DATABASE_URL`、`INTERACTION_DB_ENABLED`
2. 查 `requirement_documents`，确认源文档和解析字段是否已写入
3. 查 `usecase_workflows` 和 `usecase_workflow_snapshots`，确认工作流是否已经生成候选结果
4. 查 `use_cases`，确认最终正式用例是否已经持久化
5. 如果不想连库，改用 `/api/usecase-generation/workflows/documents` 和 `/api/usecase-generation/use-cases`

## 先读这些（当前权威）

1. `docs/service-design.md`
   - 服务职责边界、数据库策略、HTTP 契约、agent/tool 对接方式
2. `docs/usecase-workflow-design.md`
   - 用例生成目标设计：四个 subagent、review 后确认、保留附件解析产物落库

## 文档约定

- 当前目录只保留仍然指导后续实现的设计文档
- 这里描述的是 `interaction-data-service` 的目标设计，不代表代码已经落地
- 真正开始实现后，当前行为应以代码和后续补充的 `README.md` / `current-architecture.md` 为准
