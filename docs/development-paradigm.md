# 当前项目开发范式说明

## 这篇文档想讲清什么

这篇文档不重复介绍怎么启动项目，而是专门回答 3 个问题：

- 当前项目到底在解决什么工程问题
- 为什么要把平台侧、运行时、调试入口拆成现在这样
- 以后继续开发时，应该优先改哪里，按什么顺序推进

如果只用一句话概括，这个项目的核心思路就是：

> 用平台侧做治理，用运行时做智能体，用调试前端做快速验证，用结果域服务做持久化承接，几块之间通过浅封装和稳定契约连接起来，而不是揉成一个大泥球。

## 1. 这个项目真正解决什么问题

很多 Agent 项目一开始都能跑 demo，但一旦进入真实工程开发，很快就会出现几类典型问题：

- 平台治理和智能体逻辑写在一起，后面谁改都痛苦
- 调试入口和正式产品入口混在一起，导致验证链路混乱
- 权限、项目隔离、审计、catalog、运行时能力这些平台问题，反过来污染智能体代码
- 智能体结果落库直接塞进平台主数据模型，最后平台越来越重
- 本地能跑，后面一到拆服务、上容器、做独立部署就开始互相扯头花

当前仓库的设计目标，就是把这些问题提前拆开。

## 2. 一句话理解当前架构

当前默认链路可以概括成两条：

- 平台链路：`platform-web -> platform-api -> runtime-service`
- 调试链路：`runtime-web -> runtime-service`

再加上一个结果域服务：

- 持久化链路：`runtime-service -> interaction-data-service`

这说明当前仓库不是单体 Agent Demo，而是一个明确分层的企业级 AI 平台骨架：

- `platform-web` / `platform-api` 负责平台控制面
- `runtime-service` 负责智能体运行时
- `runtime-web` 负责运行时调试
- `interaction-data-service` 负责结果域数据

## 3. 为什么要这么设计

### 3.1 平台侧做浅封装，不深度侵入 Runtime

这里最容易被误解的一点，就是“平台接入 Runtime”不等于“平台吃掉 Runtime”。

当前项目里，平台侧的定位很明确：

- `platform-api` 负责认证、项目边界、成员与权限、审计、catalog、runtime policy/capability 管理
- `platform-web` 负责平台工作台界面、管理页面、聊天入口和工作区导航

而智能体真正的执行、模型装配、工具装配、MCP 接入、graph 编排，都放在 `runtime-service`。

这就叫“浅封装”。

这里的浅，不是说平台什么都不做，而是说平台只做上层治理和入口整合，不去改写智能体内部的运行模式。当前 `platform-api` 也不是历史上那种透明透传 proxy，而是保留明确的 `/api/langgraph/*` 网关，在这里做：

- 显式路由
- 必要白名单处理
- 项目边界校验
- metadata 注入
- 平台治理相关控制

这样做的好处很直接：

- 平台团队可以专注权限、管理、审计，不用被智能体实现细节拖死
- AI 开发可以专注 `runtime-service`，不必每做一个 Agent 都改一轮平台底座
- Runtime 依然保持标准 LangGraph 风格接口，后面升级和替换成本更低

### 3.2 功能解耦比“功能堆一起”更重要

当前仓库里，每个应用的边界其实已经很明确：

- `platform-web`：平台工作台、管理页面、平台聊天入口
- `platform-api`：鉴权、项目治理、审计、catalog、运行时网关
- `runtime-service`：graph 注册、模型参数解析、工具装配、MCP、智能体执行
- `runtime-web`：直连 Runtime 的调试前端
- `interaction-data-service`：结果域落库与查询

这套拆法的意义不是“服务多看起来高级”，而是为了让每一层都只承担自己该承担的责任。

平台侧不去吞智能体逻辑，运行时不去硬扛平台治理，结果域服务不去污染平台主数据，这才是后续能长期演进的前提。

### 3.3 调试链路必须独立存在

`runtime-web` 的存在不是装饰品，它解决的是一个很实际的问题：

如果每次开发智能体都必须先接完整个平台链路，你的调试成本会很高，排查问题也会混在权限、网关、页面逻辑里一起爆炸。

所以当前项目保留了独立调试链路：

- `runtime-web -> runtime-service`

这条链路的价值是：

- 先验证智能体本身是不是工作正常
- 先验证 prompt、tools、MCP、graph 编排是不是符合预期
- 先验证运行时接口是不是稳定
- 在不引入平台治理复杂度的前提下快速迭代

等你把智能体在 `runtime-web` 上调通之后，再接到 `platform-web` / `platform-api` 里，成本就会非常低。

这里所谓“零成本、无适配”，本质上指的是：

- 你开发和调试的本来就是同一个 `runtime-service`
- 平台侧消费的也是同一套 Runtime 契约
- 只要你没有绕开现有边界、私自把业务逻辑写死在平台层，那么后续接平台通常不需要重写 Agent

也就是说，真正的秘诀不是“平台魔法适配”，而是“一开始就守住边界”。

### 3.4 结果域再拆一层，平台会更轻

很多项目一做结果落库，就喜欢全塞进平台后端，最后平台侧数据库模型越来越脏，越改越重。

当前仓库选择把结果域抽到 `interaction-data-service`，核心好处有两个：

- 平台主数据和结果域数据不互相污染
- Runtime 需要持久化时，可以通过明确的 HTTP 契约写入结果域服务

这样平台侧依然可以通过 `platform-api` 聚合查询、做权限与项目隔离，但不需要亲自维护每一个智能体业务表。

### 3.5 以后改成 Docker 部署会更自然

你提到后面各部分用 Docker 方式部署，这个方向和当前设计其实是完全一致的。

因为当前已经把责任边界拆清楚了，所以后面如果做容器化部署：

- `platform-web`
- `platform-api`
- `runtime-service`
- `runtime-web`
- `interaction-data-service`

都可以按各自职责独立构建、独立部署、独立扩缩容。

换句话说，Docker 不是这套架构成立的前提，而是这套解耦架构成熟之后最自然的部署结果。

## 4. 为什么说智能体开发主战场在 `runtime-service`

当前仓库里，真正和 AI 能力强相关的内容都已经收敛到 `runtime-service`：

- graph 注册在 `runtime_service/langgraph.json`
- 运行时参数解析在 `runtime_service/runtime/options.py`
- 模型装配在 `runtime_service/runtime/modeling.py`
- 工具装配在 `runtime_service/tools/registry.py`
- MCP server 清单在 `runtime_service/mcp/servers.py`
- 业务型智能体建议放在 `runtime_service/services/<service_name>/`

更关键的是，这里不是只给了一个空壳，而是已经准备好了多种开发范式和例子：

- `assistant`：默认推荐范式，适合从最小可行 Agent 开始
- `deepagent_demo`：适合任务分解、多子任务协同
- `personal_assistant_demo`：适合 supervisor + subagent 协作
- `customer_support_handoffs_demo`：适合显式步骤流
- `sql_agent`：适合服务化 Agent 参考
- `usecase_workflow_agent`：适合业务工作流型样板

所以，后面新增智能体时，默认思路应该是：

- 先在 `runtime-service` 里实现
- 先在 `runtime-web` 或 runtime devtools 里验证
- 稳定后再挂到平台入口

不要一上来就把智能体逻辑散落到平台前后端里，那是给后面埋雷。

## 5. 为什么说几行代码就能搭一个简单智能体

`runtime-service` 已经把最麻烦的共性问题封装掉了：

- 模型选择和运行时参数处理已经有统一入口
- 公共 tools / MCP 装配已经有现成注册机制
- 多模态 middleware 已经准备好
- graph 注册方式已经固定
- 相关测试和最小验证路径也已经写好

所以，一个最小可运行 Agent 的核心代码可以非常薄。按照仓库现成的模板，一个 hello demo 的核心结构大概就是这样：

```python
from langchain.agents import create_agent


async def make_graph(config, runtime):
    del runtime
    options = build_runtime_config(config, {})
    model = apply_model_runtime_params(resolve_model(options.model_spec), options)
    tools = await build_tools(options)
    tools.append(hello_tool)
    return create_agent(model=model, tools=tools, system_prompt=options.system_prompt)


graph = make_graph
```

真正要做的事情，通常只剩下 3 步：

1. 写自己的 tool / prompt / graph 逻辑
2. 注册到 `langgraph.json`
3. 跑最小验证命令

这就是为什么说它已经不是“从零搭框架”，而是“在现成运行时骨架上扩展能力”。

## 6. 未来继续开发时，建议你按这个顺序判断

### 6.1 先判断需求属于哪一层

你以后每接一个需求，先别急着写代码，先做一个最基础的判断：

- 如果是权限、项目、成员、审计、catalog、平台配置，改 `platform-api` / `platform-web`
- 如果是 prompt、tool、MCP、graph、模型装配、Agent 行为，改 `runtime-service`
- 如果是运行时联调和交互验证，先用 `runtime-web`
- 如果是业务结果持久化与查询，改 `interaction-data-service`

这个判断做对了，后面开发基本就顺了；判断做错了，代码很快就会串层。

### 6.2 先在 Runtime 内把能力做通

新增智能体能力时，推荐顺序是：

1. 先选合适范式
2. 在 `runtime-service` 内完成 graph / tools / prompts
3. 注册 graph
4. 本地验证运行时接口
5. 用 `runtime-web` 做交互验证

如果这一步都没过，就不要急着接平台页面。

### 6.3 再决定要不要接平台入口

只有当智能体本身已经稳定后，再看平台侧要不要补：

- 管理页面
- 平台聊天入口
- assistant/graph 管理
- 项目级权限控制
- catalog 同步与治理能力

平台侧的角色应该是“把已经稳定的 Runtime 能力纳入治理和产品入口”，不是“代替 Runtime 做智能体开发”。

### 6.4 需要结果落库时，再接结果域服务

如果某个智能体只是对话验证，不一定立刻需要持久化。

但如果它进入正式业务链路，需要：

- 结构化结果沉淀
- 列表查询
- 详情展示
- 审批后落库

这时候再把结果域能力放进 `interaction-data-service`，由 Runtime 的本地 tools 通过 HTTP 调用它。

这套方式比把业务表直接硬塞进 `platform-api` 清爽得多。

### 6.5 最后再考虑部署形态

当边界都守住之后，部署方式反而简单：

- 本地联调用当前默认多服务方案
- 独立部署时按服务拆镜像和容器
- 哪个服务变化频繁，就独立迭代哪个服务

所以重点永远不是“先写 Docker”，而是“先把边界守住”。

## 7. 一定要记住的几个核心思路

最后把最重要的话直接收口成几条，后面开发时反复对照就行：

1. 平台侧是浅封装，不是把智能体运行时深度吞进去。
2. 平台侧优先专注权限、管理、审计、catalog、治理能力。
3. 智能体和 AI 相关开发，主战场永远在 `runtime-service`。
4. `runtime-web` 是调试入口，先把智能体在这里调通，再接平台。
5. 调试完成后，只要遵守现有契约，就可以无缝接入 `platform-api` / `platform-web`，不需要为平台重写一套 Agent。
6. `interaction-data-service` 负责结果域，避免平台主数据和业务结果表混成一锅粥。
7. 后面用 Docker 独立部署，是当前解耦设计的自然延伸，不是另一套新思路。
8. `runtime-service` 已经提供脚手架、范式和样例，后续开发优先仿照现有模式，不要重复造轮子。

## 8. 建议配套阅读

如果你想把这套开发范式看得更实，建议继续看这些文件：

- `README.md`
- `docs/development-guidelines.md`
- `docs/project-story.md`
- `apps/platform-api/docs/current-architecture.md`
- `apps/platform-web/README.md`
- `apps/runtime-web/README.md`
- `apps/runtime-service/runtime_service/docs/README.md`
- `apps/runtime-service/runtime_service/docs/05-template-to-runnable-agent-10min.md`
- `apps/interaction-data-service/README.md`
