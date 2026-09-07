# AI Agent Platform 开发规范

这是项目的 AI 协作入口，定义了开发流程、分级标准和验证要求。

## 快速开始

**新人必读：**
1. 阅读 `README.md` - 了解项目架构
2. 阅读 `docs/quickstart/` - 快速上手
3. 开始改动前，先使用 `/route-change` 判断级别

**核心 Skills：**
- `/route-change` - 分析改动级别，给出建议流程
- `/plan-project` - 规划新项目（链路/治理改动）
- `/implement-feature` - 实现功能并记录
- `/verify-change` - 执行验证并记录结果

## 改动分级（单项目改动/链路改动/治理改动）

### 单项目改动
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

### 链路改动
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

### 治理改动
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

### 场景1：单项目改动

```bash
# 1. 直接实现
# 编辑代码...

# 2. 单元测试
pytest apps/xxx/tests/

# 3. 提交
git commit -m "fix: 修复 xxx 问题"
```

### 场景2：链路改动

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

### 场景3：治理改动

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

## archive/ 的定义

`archive/` 只存放**已被取代、已被否决、不再是事实来源**的内容。

判断标准：这份文档现在还会被拿来对照检查代码、指导实现，还是决策吗？
- 会 → 不进 `archive/`，哪怕对应的开发阶段已经跑完（比如某阶段的设计文档，只要代码仍需要按它来验收，就还是有效事实源）
- 不会 → 进 `archive/`（比如被新方案替换的旧设计、废弃的旧架构说明、过时的排期计划）

反例：不要因为"这个阶段做完了"就把设计文档丢进 `archive/`——阶段完成不等于文档作废，完成状态应该写在项目文档（`docs/projects/{项目名}/README.md` 或 `tasks.md`）里，不要靠挪目录来表达。

## 项目进度标注（替代复杂的 archive 流程）

不需要单独的归档审批流程。项目进度直接在项目文档里如实标注：

- 在 `tasks.md` 的任务前用 `[x]`/`[ ]` 标注完成状态
- 在 `README.md` 的"状态"字段写清楚：规划中 / 进行中 / 已完成 / 部分完成（并说明哪部分未完成）
- 未完成或明确推迟的部分，直接在文档里写清楚原因（阻塞、后置、超出本阶段范围），不要略过不提
- 项目全部完成后，文档保留在 `docs/projects/` 下即可，不强制搬到 `archive/`；只有当项目被后续方案整体取代、文档不再指导任何当前实现时才移入 `archive/`

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
├── projects/                   # 项目文档（链路/治理改动）
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

### 单项目改动
- ✅ 单元测试通过
- ✅ 代码质量检查通过（lint、类型检查）

### 链路改动
- ✅ 单元测试通过
- ✅ 集成测试通过
- ✅ 端到端测试通过（至少一条完整链路）

### 治理改动
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
   - 使用 `/route-change` 分析级别
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
   - 完成的项目在 `README.md`/`tasks.md` 里如实标注进度，不强制搬目录
   - 只有被取代、不再是事实源的内容才移入 `archive/`（见"archive/ 的定义"）
   - 保持文档数量可控

## 注意事项

- 判断级别看影响范围，不看代码量
- 治理改动必须有评审批准
- 验证通过才能合并代码
- 文档是给其他人看的，要清晰易懂
