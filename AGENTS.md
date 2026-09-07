# AI Agent Platform 开发规范

这是项目的 AI 协作入口，定义了开发流程、分级标准和验证要求。

## 快速开始

**新人必读：**
1. 阅读 `README.md` - 了解项目架构
2. 阅读 `docs/quickstart/` - 快速上手
3. 开始改动前，先使用 `/route` 判断级别

**核心 Skills：**
- `/route` - 分析改动级别，给出建议流程
- `/plan-project` - 规划新项目（B2/B3 级）
- `/implement-feature` - 实现功能并记录
- `/verify-change` - 执行验证并记录结果

## 改动分级（B1/B2/B3）

### B1 Local（本地改动）
**范围：** 单服务内部，不影响对外契约

**流程：**
```
直接实现 → 单元测试 → Commit
```

**文档：** 无需项目文档，commit message 即可

**示例：**
- 重构内部函数
- 优化算法
- 修复单服务内 bug
- 添加日志

---

### B2 Chain（链路改动）
**范围：** 跨服务改动，影响服务间契约或数据模型

**流程：**
```
/plan-project → 实现 → 链路测试 → /verify-change
```

**文档：** 需要在 `docs/projects/` 下创建项目目录

**验证要求：**
- ✅ 单元测试
- ✅ 集成测试
- ✅ 端到端测试（至少一条完整链路）

**示例：**
- runtime-service 契约变更
- platform-api 新增接口
- 数据库表结构调整
- 跨服务功能开发

---

### B3 Governed（治理级改动）
**范围：** 影响架构、安全、生产环境、数据迁移

**流程：**
```
/plan-project → 方案评审 → 批准 → 实施 → 全面验证 → /verify-change
```

**文档：** 完整项目文档 + 评审记录

**验证要求：**
- ✅ 单元测试
- ✅ 集成测试
- ✅ 端到端测试（所有关键链路）
- ✅ 性能测试（如适用）
- ✅ 安全测试（如适用）
- ✅ 回滚方案验证

**示例：**
- 架构重构
- 数据库迁移
- 安全加固
- 生产发布流程
- 鉴权系统改造

## 服务边界

当前仓库包含 4 个核心服务：

### platform-web
**职责：** 正式平台前端、管理页面、平台聊天入口

**标准文档：**
- `apps/platform-web/docs/frontend-development-playbook.md`
- `apps/platform-web/docs/control-plane-page-standard.md`

### platform-api
**职责：** 鉴权、项目治理、审计、catalog、运行时网关

**标准文档：**
- `apps/platform-api/docs/handbook/*.md`
- `apps/platform-api/docs/standards/*.md`

### runtime-service
**职责：** graph 注册、模型参数解析、工具装配、MCP、智能体执行

**标准文档：**
- `apps/runtime-service/docs/standards/*.md`
- `apps/runtime-service/tests/*.py`（可执行契约）

### interaction-data-service
**职责：** 结果域落库与查询

**标准文档：**
- `apps/interaction-data-service/docs/test-case-service-api-design.md`
- `apps/interaction-data-service/docs/standards/result-domain-boundary-standard.md`

## 主要链路

```
platform-web → platform-api → runtime-service → interaction-data-service
```

## 开发流程

### 场景1：B1 级小改动

```bash
# 1. 直接实现
# 编辑代码...

# 2. 单元测试
pytest apps/xxx/tests/

# 3. 提交
git commit -m "fix: 修复 xxx 问题"
```

### 场景2：B2 级链路改动

```bash
# 1. 规划项目
AI: /plan-project
User: runtime-service 数据建模重构

# 2. 完善文档
# 编辑 docs/projects/runtime-modeling-refactor/plan.md
# 编辑 docs/projects/runtime-modeling-refactor/tasks.md

# 3. 实现功能
AI: /implement-feature
# AI 实现并记录到 implementation/

# 4. 验证
AI: /verify-change
# AI 执行测试并记录到 verification.md

# 5. 提交
git commit -m "refactor(runtime): 重构数据建模

详见 docs/projects/runtime-modeling-refactor/"
```

### 场景3：B3 级治理改动

```bash
# 1. 完整规划
AI: /plan-project
# 生成完整项目文档

# 2. 方案评审
# 团队评审 plan.md
# 批准后在 README.md 记录评审结果

# 3. 分阶段实施
# Phase 1...
# Phase 2...

# 4. 全面验证
AI: /verify-change
# 执行所有级别的测试

# 5. 生产部署（如适用）
# 按部署流程执行

# 6. 归档
# 项目完成后精简文档，保留关键决策
```

## 文档组织

```
docs/
├── README.md                   # 文档导航
├── quickstart/                 # 快速开始（新人必读）
│   ├── architecture.md
│   ├── local-dev.md
│   └── deployment.md
├── guides/                     # 开发指南
│   ├── development-workflow.md
│   ├── coding-standards.md
│   └── configuration.md
├── projects/                   # 项目文档（B2/B3 级）
│   └── {project-name}/
│       ├── README.md          # 项目概览
│       ├── plan.md            # 整体方案
│       ├── tasks.md           # 任务拆分
│       ├── verification.md    # 验证记录
│       └── implementation/    # 实现细节
├── decisions/                  # 技术决策（ADR）
└── archive/                    # 归档文档
```

## 验证标准

### B1 Local
- ✅ 单元测试通过
- ✅ 代码质量检查通过（lint、类型检查）

### B2 Chain
- ✅ 单元测试通过
- ✅ 集成测试通过
- ✅ 端到端测试通过（至少一条完整链路）

### B3 Governed
- ✅ 单元测试通过
- ✅ 集成测试通过
- ✅ 端到端测试通过（所有关键链路）
- ✅ 性能测试通过（如适用）
- ✅ 安全测试通过（如适用）
- ✅ 回滚方案验证（如适用）

## LangChain 生态系统文档

对于 LangGraph、LangChain、DeepAgents 的 API 使用、示例、错误、迁移或最佳实践问题，
先查询 `langchain-docs` 和 `langchain-reference` MCP，再提出实现代码。

## 最佳实践

1. **改动前先路由**
   - 使用 `/route` 分析级别
   - 按建议流程执行

2. **文档写清楚**
   - 文件路径要完整
   - 函数名要准确
   - 改动理由要说明

3. **验证要真实**
   - 不编造测试结果
   - 发现问题如实记录
   - 保留验证证据

4. **定期清理**
   - 完成的项目精简文档
   - 过时内容移到 archive/
   - 保持文档数量可控

## 注意事项

- 判断级别看影响范围，不看代码量
- B3 级改动必须有评审批准
- 验证通过才能合并代码
- 文档是给其他人看的，要清晰易懂
