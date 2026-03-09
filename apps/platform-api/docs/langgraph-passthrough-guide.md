# LangGraph 同构入参与出参透传教学文档

## 1. 这份文档讲什么

这份文档专门解释本仓库里“LangGraph 请求/响应透传”这件事是怎么做的，重点参考：

- `app/api/langgraph/__init__.py`
- `app/api/langgraph/assistants.py`
- `app/api/langgraph/threads.py`
- `app/api/langgraph/runs.py`
- `app/api/frontend_passthrough.py`
- `app/api/proxy/runtime_passthrough.py`

如果你之前对“同构入参 / 同构出参”不熟，这里先给一句最短解释：

> 调用方传什么核心业务字段，上游 LangGraph 就尽量收到什么；上游返回什么核心结果，调用方也尽量拿到什么。

这里的“同构”不是说 100% 字节级不变，而是说：

- **业务字段语义尽量不变**
- **路径语义尽量不变**
- **响应主体尽量不重写**
- **只在必要处做最小改写**（比如补头、做鉴权边界、SSE 包装、兼容前端格式）

---

## 2. 先理解：仓库里其实有两种透传

本项目里和 LangGraph 相关的入口，不是只有一种。

### 2.1 第一种：SDK 风格的“半透传”接口

代码入口：

- `app/api/langgraph/__init__.py`
- `app/api/langgraph/assistants.py`
- `app/api/langgraph/threads.py`
- `app/api/langgraph/runs.py`

这类接口的特点是：

- 路由是本项目自己定义的，例如 `/api/langgraph/runs`。
- 参数主体仍然尽量沿用 LangGraph 原生字段。
- 代码会做**少量字段筛选、项目边界校验、元数据注入、SSE 包装**。
- 最终不是直接自己拼 HTTP，而是通过 `langgraph_sdk` 调上游。

它更像：

> “保留 LangGraph 参数语义，但在我方服务边界上加一点安全与治理能力。”

### 2.2 第二种：HTTP 原样透传接口

代码入口：

- `app/api/frontend_passthrough.py`
- `app/api/proxy/runtime_passthrough.py`
- `app/factory.py`

这类接口的特点是：

- 收到什么 HTTP 方法、路径、请求体，就尽量原样转发给上游。
- 上游返回什么状态码、响应头、响应体，就尽量原样回给调用方。
- 特别适合前端已经按 LangGraph API 调用、不想改请求结构的场景。

它更像：

> “我自己不理解业务对象，只负责把 HTTP 来回搬运好。”

---

## 3. 图解：整条链路怎么走

```text
+------------------+      HTTP Request       +---------------------------+
| 调用方           | ---------------------> | FastAPI 代理层            |
| 前端 / SDK / curl |                        |                           |
|                  |                        | 1) app/api/langgraph/*    |
|                  |                        |    - SDK 风格半透传        |
|                  |                        |    - 字段筛选/权限校验      |
|                  |                        |                           |
|                  |                        | 2) app/api/frontend_*     |
|                  |                        |    - 前端兼容封装          |
|                  |                        |    - 原始 LangGraph 透传   |
|                  |                        |                           |
|                  |                        | 3) app/api/proxy/*        |
|                  |                        |    - 更底层 HTTP 透传      |
+------------------+                        +-------------+-------------+
                                                         |
                                                         | httpx / langgraph_sdk
                                                         v
                                            +---------------------------+
                                            | LangGraph Upstream        |
                                            | 真正执行 assistant/thread |
                                            | /run 的服务               |
                                            +---------------------------+
```

如果把这三层再压缩成人话：

- `app/api/langgraph/*`：偏“治理型同构透传”
- `app/api/frontend_passthrough.py`：偏“前端兼容型透传”
- `app/api/proxy/runtime_passthrough.py`：偏“底层 HTTP 原样透传”

---

## 4. 路由装配：请求是怎么进来的

在 `app/factory.py` 里，几个关键入口都被挂进 FastAPI：

- `management_router`
- `langgraph_router`
- `frontend_passthrough_router`
- `/_runtime/{full_path:path}`
- `/{full_path:path}`

这里最关键的事实有两个：

### 4.1 `/api/langgraph/*` 是显式路由

`app/api/langgraph/__init__.py` 把下面几类能力挂在了 `/api/langgraph` 前缀下：

- assistants
- graphs
- threads
- runs

也就是说：

- `POST /api/langgraph/runs`
- `POST /api/langgraph/threads`
- `POST /api/langgraph/assistants/search`

这类路径不是“盲转发”，而是代码里明确实现的 API。

### 4.2 `/{full_path:path}` 和 `/_runtime/{full_path:path}` 是兜底透传

在 `app/factory.py` 里，最后还有两个非常宽的入口：

- `/_runtime/{full_path:path}`
- `/{full_path:path}`

它们最终都走 `app/api/proxy/runtime_passthrough.py` 里的 `passthrough_request()`。

这意味着：

- 如果请求没有被前面更具体的路由吃掉，最后就会走到底层透传。
- 这是“透明代理”能力成立的关键。

一句话：

> 明确治理的走显式路由；不想改路径的走兜底透传。

---

## 5. 什么叫“同构入参”

“同构入参”不是说所有字段都无脑 `request.body()` 原封不动往上扔，而是指：

- 上游 LangGraph 认识的业务字段，尽量继续用上游的命名和结构。
- 代理层只做最小必要加工。

### 5.1 在 `app/api/langgraph/*` 里的做法

以 `app/api/langgraph/runs.py` 为例：

- `POST /api/langgraph/runs`
- `POST /api/langgraph/runs/wait`
- `POST /api/langgraph/runs/stream`

这些接口都要求 `payload` 是对象，并保留 LangGraph 核心字段，比如：

- `assistant_id`
- `input`
- `command`
- `stream_mode`
- `metadata`
- `config`
- `context`
- `checkpoint`
- `interrupt_before`
- `interrupt_after`

真正的字段白名单定义在：

- `app/services/langgraph_sdk/runs_service.py`

这里的模式是：

1. 路由层先做最基本的必填校验，例如 `assistant_id is required`
2. 路由层做项目边界校验，例如 `assert_assistant_belongs_project()`
3. service 层只挑出允许透传的字段
4. 最后调用 `langgraph_sdk` 的对应方法

所以这里的“同构”更准确地说是：

> **同构字段语义 + 白名单透传**

不是无限制透传。

### 5.2 在线程接口里的做法

以 `app/api/langgraph/threads.py` 为例：

- 创建 thread 时允许的字段在 `LangGraphThreadsService._CREATE_FIELDS`
- 搜索 thread 时允许的字段在 `LangGraphThreadsService._SEARCH_FIELDS`
- 更新 state 时允许的字段在 `LangGraphThreadsService._UPDATE_STATE_FIELDS`

此外还有一个很关键的增强：

- `inject_project_metadata()` 会在 scope guard 打开时，把 `project_id` 注入到 `metadata`

这说明它不是纯透传，而是：

- **尽量保持 LangGraph 原生参数结构**
- **在 metadata 上附加我方项目边界信息**

### 5.3 在线路由透传里的做法

在 `app/api/proxy/runtime_passthrough.py` 里，逻辑更接近原样转发：

1. 读取 `request.method`
2. 拼接上游 URL
3. 读取 `await request.body()`
4. 复制请求头，去掉 hop-by-hop 头和 `host` / `content-length`
5. 通过 `httpx` 把同样的方法、体和头发给上游

这里的“同构入参”就更接近：

> HTTP 方法、路径、query、body 都尽量不改。

---

## 6. 什么叫“同构出参”

“同构出参”也分两层理解。

### 6.1 SDK 风格路由的出参

在 `app/api/langgraph/*` 里，大多数返回值最终会经过：

- `jsonable_encoder(...)`

这一步的意义不是改业务语义，而是把 SDK 返回的对象变成 FastAPI 可以安全输出的 JSON 结构。

例如：

- create assistant → 返回 assistant 对象
- get thread → 返回 thread 对象
- wait run → 返回 run 完成结果

这类接口的出参原则是：

- **业务对象语义尽量保持和上游一致**
- **返回格式转换为标准 JSON 可序列化结构**

另外有少量兼容性回退：

- delete 场景里如果上游返回 `None`，本地会补成 `{"ok": true}`

这是为了让调用方有稳定的成功语义。

### 6.2 HTTP 透传路由的出参

在 `app/api/proxy/runtime_passthrough.py` 里，出参更接近真正的“原样透传”：

- 保留上游状态码
- 保留大部分响应头
- 过滤 hop-by-hop 头和 `content-length`
- 直接把上游字节流流回客户端

也就是说：

> 上游是 200，你基本就拿到 200；上游是 SSE，你基本就拿到 SSE；上游是长响应流，你基本就拿到长响应流。

---

## 7. Header 是怎么透传的

Header 透传是这套系统能否“像原生 LangGraph 一样工作”的关键。

### 7.1 SDK 客户端模式

`app/services/langgraph_sdk/client.py` 会转发这些头：

- `authorization`
- `x-tenant-id`
- `x-project-id`
- `x-request-id`

如果请求里没有 `x-request-id`，但中间件已经在 `request.state.request_id` 上挂了值，也会自动补上。

这背后的意义：

- `authorization`：透传用户认证上下文
- `x-tenant-id` / `x-project-id`：透传租户/项目边界
- `x-request-id`：保证链路可追踪

### 7.2 HTTP 透传模式

`app/api/proxy/runtime_passthrough.py` 的处理方式是：

- 请求头整体复制
- 删除 hop-by-hop 头
- 删除 `host`
- 删除 `content-length`
- 注入 `x-request-id`
- 如果配置了 `LANGGRAPH_UPSTREAM_API_KEY`，再补 `x-api-key`

这是一种更底层、更通用的透传策略。

### 7.3 前端兼容透传模式

`app/api/frontend_passthrough.py` 的 `_forward_headers()` 更保守，只显式转发：

- `accept`
- `content-type`
- `authorization`
- `x-tenant-id`
- `x-project-id`
- `x-request-id`
- 可选 `x-api-key`

这说明前端兼容层不是为了“全头透传”，而是为了“稳定透传最关键头”。

---

## 8. Body 是怎么透传的

### 8.1 底层 HTTP 透传

在 `app/api/proxy/runtime_passthrough.py` 里：

- `body = await request.body()`
- 然后 `content=body` 发给上游

也就是说：

- JSON body 可以过
- 文本 body 可以过
- 二进制 body 也可以过

只要上游理解这个 body，代理层通常不拦。

### 8.2 前端兼容透传

在 `app/api/frontend_passthrough.py` 里，原始透传分支也是：

- 读原始 body
- 原样带给上游

如果 body 为空，还会把 `content-type` 删掉，避免空 body 还带 JSON 头导致上游误判。

### 8.3 SDK 风格透传

`app/api/langgraph/*` 不是把原始字节 body 整包上传，而是先把 body 解析为 Python 对象，再通过字段白名单传给 SDK。

这就是它和底层 HTTP 透传最大的区别：

- HTTP 透传：偏字节级搬运
- SDK 透传：偏业务字段级搬运

---

## 9. 流式响应（SSE）为什么是重点

如果只会处理 JSON，请求代理并不难；真正容易出问题的是流式响应。

### 9.1 在 `app/api/langgraph/runs.py` 里的流式处理

`POST /api/langgraph/runs/stream` 会：

1. 调 `service.stream_global(payload)`
2. 拿到 SDK 的事件迭代器
3. 用 `_sse_stream()` 包装成 `StreamingResponse`

其中 `_to_sse_chunk()` 会把不同类型事件转成合法 SSE：

- `bytes`
- `str`
- `(event_name, event_data, event_id)` 元组
- 普通对象

这一步的本质是：

> SDK 世界里的“事件对象”，要翻译成 HTTP 世界里的 `text/event-stream` 字节块。

### 9.2 在 `app/api/frontend_passthrough.py` 里的流式处理

`GET /api/chat/stream` 会直接请求上游：

- `POST /threads/{thread_id}/runs/stream`

然后：

- 如果上游出错，先读取完整错误体并抛出 `HTTPException`
- 如果上游成功，就 `aiter_raw()` 按块把流回传给前端
- 同时额外补一个响应头：`x-thread-id`

所以这里的模式是：

- **请求体是本地组装出来的 LangGraph run payload**
- **响应体是上游 SSE 字节流基本原样转发**

### 9.3 在底层 `runtime_passthrough` 里的流式处理

`app/api/proxy/runtime_passthrough.py` 里，对所有响应统一采用 `stream=True`。

然后通过：

- `upstream_response.aiter_raw()`

把数据持续流给客户端。

这也是 README 里那句 “SSE and long responses are streamed through directly” 的真正落点。

---

## 10. 这套设计到底“改了什么，没改什么”

这是最容易混淆的地方。

### 10.1 尽量没改的部分

- HTTP method
- 业务路径语义
- query string
- LangGraph 核心字段命名
- 上游主要返回对象
- SSE 流式语义

### 10.2 明确改了的部分

- 补充或筛选 header
- 注入 `x-request-id`
- 可选补 `x-api-key`
- scope guard 打开时注入 `metadata.project_id`
- delete 返回 `None` 时回退成 `{"ok": true}`
- SDK 事件转换为 SSE chunk
- 某些前端兼容接口会重新包装结果，例如 `{"items": ...}`、`{"item": ...}`

所以最准确的说法不是“绝对原样”，而是：

> **对 LangGraph 业务协议尽量同构，对平台代理边界做最小必要增强。**

---

## 11. 给新同学的 3 个实际例子

### 11.1 例子一：创建 run 并等待结果

请求：

```bash
curl -X POST http://127.0.0.1:2024/api/langgraph/runs/wait \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <token>' \
  -d '{
    "assistant_id": "asst_xxx",
    "input": {"messages": [{"role": "human", "content": "hello"}]},
    "config": {"temperature": 0}
  }'
```

链路：

1. 进入 `app/api/langgraph/runs.py`
2. 校验 `assistant_id`
3. 做项目边界校验
4. `LangGraphRunsService.wait_global()` 只挑允许字段
5. `langgraph_sdk` 调用上游 `runs.wait`
6. 返回结果经 `jsonable_encoder` 输出

### 11.2 例子二：前端聊天流式输出

请求：

```bash
curl -N 'http://127.0.0.1:2024/api/chat/stream?message=hello&assistant_id=asst_xxx'
```

链路：

1. 进入 `app/api/frontend_passthrough.py`
2. 如无 `thread_id`，先创建 thread
3. 组装 LangGraph `runs/stream` payload
4. 直接请求上游 `/threads/{thread_id}/runs/stream`
5. 把 SSE chunk 原样流回前端

### 11.3 例子三：完全按原始路径透传

如果前端或调用方直接请求本代理服务上的原始 LangGraph 风格路径，且没有被更具体路由优先匹配，就可能落到：

- `/_runtime/{full_path:path}`
- `/{full_path:path}`

这时 `runtime_passthrough.py` 会尽量保留原始 HTTP 形态，把请求直接转给上游。

---

## 12. 你在开发时应该怎么选入口

### 12.1 想保留我方治理逻辑，就用 `/api/langgraph/*`

适合场景：

- 需要项目边界控制
- 需要 metadata 注入
- 需要更稳定的 SDK 字段白名单
- 需要本项目定义的接口语义

### 12.2 想兼容前端 agent-chat-ui 风格接口，就看 `app/api/frontend_passthrough.py`

适合场景：

- 前端页面已经依赖这些接口
- 你希望返回结构更贴近前端消费方式
- 你需要聊天线程、消息历史、assistants 列表等兼容封装

### 12.3 想做真正底层 HTTP 代理，就看 `runtime_passthrough.py`

适合场景：

- 不想维护一堆显式业务路由
- 调用方本来就按上游协议发请求
- 你只想代理，不想翻译业务对象

---

## 13. 常见误区

### 13.1 “同构透传”不等于“完全不处理”

错误理解：

- 代理层什么都不做，才叫透传。

本仓库真实做法：

- 为了安全、治理、兼容前端，代理层会做最小必要加工。

### 13.2 “SDK 路由”和“HTTP 盲透传”不是一回事

错误理解：

- 只要最终到了 LangGraph，就都一样。

真实区别：

- SDK 路由按字段级透传
- HTTP 透传按请求/响应级透传

### 13.3 “返回长得像 JSON”不代表没有改造

有些接口虽然最后返回的也是 JSON，但中间可能已经做过：

- 白名单筛选
- 元数据注入
- 删除回退包装
- 前端兼容结构包装

所以判断是否“同构”，不要只看最后长相，要看链路。

---

## 14. 最后用一句话记住这套设计

> `app/api/langgraph` 负责“带治理的同构透传”，`app/api/proxy/runtime_passthrough` 负责“更底层的 HTTP 原样透传”，`app/api/frontend_passthrough` 负责“给前端好用的兼容型透传”。

如果你以后读到这几层代码时觉得有点像，那是对的；如果你觉得它们完全一样，那就不对。
