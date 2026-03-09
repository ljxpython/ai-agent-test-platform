# Chat 图片与文件上传链路说明

## 1. 这份文档解决什么问题

这份文档专门解释当前聊天页面里“上传图片 / 上传 PDF 文件”这件事，系统到底是怎么处理的。

它重点回答 4 个问题：

- 前端上传图片或 PDF 后，会不会先把文件传到某个文件服务？
- 平台层最终收到的到底是什么数据？
- 图片和 PDF 的处理有什么区别？
- 如果未来要支持更多文件类型，当前代码是否需要修改？

对应代码入口主要有：

- `agent-chat-ui/src/components/thread/index.tsx`
- `agent-chat-ui/src/hooks/use-file-upload.tsx`
- `agent-chat-ui/src/lib/multimodal-utils.ts`
- `agent-chat-ui/src/components/thread/MultimodalPreview.tsx`
- `agent-chat-ui/src/providers/Stream.tsx`
- `app/api/langgraph/runs.py`
- `app/services/langgraph_sdk/runs_service.py`

---

## 2. 先说结论

当前实现里：

- 图片和 PDF **都不会先单独上传到对象存储或文件服务**。
- 前端会直接在浏览器里把文件读成 **base64**。
- 然后把它包装成 LangGraph 风格的多模态消息块。
- 最后和文本一起，作为一次 chat run 的 `input.messages` 发给平台。

也就是说，平台层收到的不是：

- `multipart/form-data`
- 浏览器 `File` 对象
- 原始二进制流
- 文件 URL

而是：

- **JSON 请求体**
- JSON 里的 **base64 文件内容**
- 以及对应的 `mimeType`、文件名等元数据

一句人话概括：

> 当前系统不是“先上传文件，再发引用”，而是“把文件直接塞进消息里一起发”。

---

## 3. 图解：整条上传链路怎么走

```text
+------------------+
| 用户在 Chat 页面   |
| 选择/拖拽/粘贴文件 |
+---------+--------+
          |
          v
+-------------------------------+
| useFileUpload()               |
| 1) 校验类型                   |
| 2) 检查是否重复               |
| 3) 调 fileToContentBlock()    |
+---------------+---------------+
                |
                v
+-------------------------------------------+
| fileToBase64()                            |
| FileReader.readAsDataURL(file)            |
| 去掉 data:*;base64, 前缀                   |
| 只保留纯 base64                            |
+----------------+--------------------------+
                 |
                 v
+-------------------------------------------+
| 生成多模态 content block                   |
| 图片 -> type: image                        |
| PDF  -> type: file                         |
+----------------+--------------------------+
                 |
                 v
+-------------------------------------------+
| handleSubmit()                             |
| 组装 newHumanMessage.content               |
| 文本块 + 图片块/PDF块                      |
+----------------+--------------------------+
                 |
                 v
+-------------------------------------------+
| stream.submit(...)                         |
| SDK 包装成 runs/stream 请求                |
| body 内核心字段是 assistant_id + input     |
+----------------+--------------------------+
                 |
                 v
+-------------------------------------------+
| 平台层 /api/langgraph/threads/.../runs/... |
| 收到 JSON                                  |
| 继续按 LangGraph run payload 透传          |
+-------------------------------------------+
```

### 3.1 ASCII 时序图：前端 -> 平台 -> LangGraph

```text
+--------+                        +-------------------+                        +------------------+
| 前端   |                        | 平台层            |                        | LangGraph 上游   |
| Chat UI|                        | FastAPI Proxy     |                        | Runtime          |
+--------+                        +-------------------+                        +------------------+
    |                                        |                                             |
    | 1. 选择/粘贴/拖拽 图片或 PDF             |                                             |
    |--------------------------------------->|                                             |
    |                                        |                                             |
    | 2. 浏览器本地读取 File                  |                                             |
    | 3. 转 base64                            |                                             |
    | 4. 组装 content block                   |                                             |
    |    - image / file                       |                                             |
    |                                        |                                             |
    | 5. stream.submit(...)                   |                                             |
    |--------------------------------------->|                                             |
    |                                        |                                             |
    |    POST /api/langgraph/threads/{id}/runs/stream                                      |
    |    JSON body:                           |                                             |
    |    - assistant_id                       |                                             |
    |    - input.messages                     |                                             |
    |    - content[].data = base64            |                                             |
    |    - content[].mimeType                 |                                             |
    |    - content[].metadata                 |                                             |
    |                                        |                                             |
    |                                        | 6. 校验 assistant/thread 归属                |
    |                                        | 7. 保留 input/config/context 等顶层字段      |
    |                                        | 8. 继续调用 LangGraph SDK / 上游 HTTP        |
    |                                        |-------------------------------------------->|
    |                                        |                                             |
    |                                        |    POST /threads/{id}/runs/stream            |
    |                                        |    JSON body 基本同构：                      |
    |                                        |    - assistant_id                            |
    |                                        |    - input.messages                          |
    |                                        |    - 图片/PDF 仍是 base64                    |
    |                                        |                                             |
    |                                        |<--------------------------------------------|
    | 9. SSE / stream events 回流             |                                             |
    |<---------------------------------------|                                             |
    |                                        |                                             |
+--------+                        +-------------------+                        +------------------+
```

这张时序图要表达的关键点只有两个：

- **文件内容在前端就已经被转成 base64**，不是平台层帮你转的。
- **平台层主要做 run 请求透传与边界校验**，不是单独做文件存储或文件解析。

---

## 4. 前端上传入口在哪里

聊天页面上传相关的 UI 在：

- `agent-chat-ui/src/components/thread/index.tsx`

这里有 3 个入口：

### 4.1 文件选择

隐藏的 `<input type="file">` 绑定到：

- `onChange={handleFileUpload}`

支持的 `accept` 目前写死为：

- `image/jpeg`
- `image/png`
- `image/gif`
- `image/webp`
- `application/pdf`

### 4.2 粘贴上传

聊天输入框绑定：

- `onPaste={handlePaste}`

也就是说，你把图片从剪贴板直接粘贴进输入框，当前系统是支持的。

### 4.3 拖拽上传

`useFileUpload()` 里还注册了全局 drag/drop 事件。

所以把文件拖进聊天区域，也会走同一套处理逻辑。

---

## 5. 当前支持哪些类型

白名单定义在：

- `agent-chat-ui/src/hooks/use-file-upload.tsx`

当前只支持：

- JPEG
- PNG
- GIF
- WEBP
- PDF

这意味着：

- Word
- Excel
- TXT
- CSV
- 音频
- 视频

这些现在都不在白名单里，默认不会通过。

---

## 6. 上传后前端会做哪些处理

核心逻辑在：

- `agent-chat-ui/src/hooks/use-file-upload.tsx`

### 6.1 先做类型校验

不在白名单里的文件会直接 toast 提示错误，不会加入消息。

### 6.2 再做重复文件检测

当前重复判断规则不是看文件内容哈希，而是：

- 图片：`type === image` + `metadata.name === file.name` + `mimeType` 相同
- PDF：`type === file` + `metadata.filename === file.name` + `mimeType === application/pdf`

也就是说，当前“重复”判断偏向 UI 级去重，不是内容级去重。

### 6.3 把文件转成 base64

转换逻辑在：

- `agent-chat-ui/src/lib/multimodal-utils.ts`

这里做的事情是：

1. 用 `FileReader.readAsDataURL(file)` 读取文件
2. 得到类似：

```text
data:image/png;base64,iVBORw0KGgoAAA...
```

3. 再把前缀去掉，只保留真正的 base64 内容

也就是最终存进消息块里的不是完整 data URL，而是：

```text
iVBORw0KGgoAAA...
```

---

## 7. 图片会被包装成什么数据

图片最终会被转成这样的消息块：

```ts
{
  type: "image",
  mimeType: file.type,
  data: "<base64字符串，无 data: 前缀>",
  metadata: { name: file.name },
}
```

对应逻辑在：

- `agent-chat-ui/src/lib/multimodal-utils.ts`

当前图片走的是多模态消息里的 `image` 类型，而不是 `file` 类型。

---

## 8. PDF 会被包装成什么数据

PDF 最终会被转成这样的消息块：

```ts
{
  type: "file",
  mimeType: "application/pdf",
  data: "<base64字符串，无 data: 前缀>",
  metadata: { filename: file.name },
}
```

这和图片最大的区别有两个：

- 图片用 `type: "image"`
- PDF 用 `type: "file"`

以及元数据字段也不同：

- 图片：`metadata.name`
- PDF：`metadata.filename`

---

## 9. 上传后，前端页面上看到的预览是什么

预览组件在：

- `agent-chat-ui/src/components/thread/ContentBlocksPreview.tsx`
- `agent-chat-ui/src/components/thread/MultimodalPreview.tsx`

### 9.1 图片预览

图片预览不是重新请求服务端地址，而是前端本地重新拼出一个 data URL：

```ts
const url = `data:${block.mimeType};base64,${block.data}`;
```

然后直接交给 `next/image` 去展示。

### 9.2 PDF 预览

PDF 当前不是做内容预览，而是显示：

- 文件图标
- 文件名
- 删除按钮

这说明当前 PDF 上传能力是“把 PDF 作为消息附件发出去”，不是“在前端内嵌 PDF 阅读器”。

---

## 10. 提交消息时，请求里长什么样

聊天提交逻辑在：

- `agent-chat-ui/src/components/thread/index.tsx`

提交时会构造一个 `newHumanMessage`：

```ts
{
  id: uuid,
  type: "human",
  content: [
    { type: "text", text: "用户输入的文本" },
    ...contentBlocks,
  ]
}
```

这里的关键点是：

- 文本和图片/PDF 在同一个 `content` 数组里
- 所以上游看到的是一条“多模态 human message”
- 如果没有输入文本，`content` 里也可以只有图片块或 PDF 块

然后前端调用：

```ts
stream.submit(
  { messages: [...toolMessages, newHumanMessage], context },
  { config, streamMode, streamSubgraphs, streamResumable }
)
```

---

## 11. 平台层最终收到哪些数据

这部分要分两层理解。

### 11.1 SDK 最终发出的 run body

`stream.submit(...)` 不会直接把第一参数裸发出去。

LangGraph SDK 会把它包装成 run 请求，核心形状是：

```json
{
  "assistant_id": "<assistantId>",
  "input": {
    "messages": [
      {
        "id": "<uuid>",
        "type": "human",
        "content": [
          { "type": "text", "text": "可选文本" },
          {
            "type": "image",
            "mimeType": "image/png",
            "data": "<base64>",
            "metadata": { "name": "demo.png" }
          }
        ]
      }
    ]
  },
  "context": { "...": "..." },
  "config": { "...": "..." },
  "stream_mode": ["messages", "values"],
  "stream_subgraphs": true,
  "stream_resumable": true
}
```

如果是 PDF，则 `content` 里的块会变成：

```json
{
  "type": "file",
  "mimeType": "application/pdf",
  "data": "<base64>",
  "metadata": { "filename": "a.pdf" }
}
```

### 11.2 平台层会不会再改写文件内容

当前不会。

后端关键路径：

- `app/api/langgraph/runs.py`
- `app/services/langgraph_sdk/runs_service.py`

平台层会做的是：

- 校验 `assistant_id`
- 校验 thread / assistant 的项目归属
- 对 top-level run 字段做白名单透传

但它**不会**：

- 把 base64 文件落盘
- 把文件上传到 OSS / S3
- 把 base64 转成 URL
- 把 PDF 自动抽文本
- 把图片自动做 OCR

换句话说，平台真正看到的是：

> **JSON 里的多模态消息块，其中包含 base64 文件内容。**

---

## 12. 所以，图片上传后系统“对图片做了哪些操作”

如果只看当前这套代码，上传图片后系统做的事情非常具体，也非常有限：

1. 校验是不是允许的图片类型
2. 检查是不是重复上传
3. 把图片读成 base64
4. 包成 `type: image` 的消息块
5. 在前端本地做预览
6. 跟文本一起发进 LangGraph run payload

当前系统**没有额外做**：

- 压缩
- 缩放
- 裁剪
- OCR
- EXIF 解析
- 图像标签提取
- 单独文件上传

所以“上传图片后，系统有没有分析图片内容”这个问题，答案是：

> **当前前端和平台层本身没有分析，它只是把图片作为多模态输入交给上游 LangGraph / 模型链路。**

---

## 13. PDF 上传后系统“对 PDF 做了哪些操作”

当前也类似，只有这些动作：

1. 校验是否为 `application/pdf`
2. 检查重复文件
3. 转 base64
4. 包成 `type: file` 的消息块
5. 前端显示文件名预览
6. 随消息一起发给平台和上游

当前系统**没有额外做**：

- 自动抽取 PDF 文本
- 自动分页解析
- 自动生成缩略图
- 自动转 markdown
- 自动做向量化

所以 PDF 现在只是“作为文件型消息内容被传过去”，并不是“平台已经内置了 PDF 理解能力”。

---

## 14. 如果未来要支持更多类型，当前代码是否需要修改

答案是：**需要，而且不只是改一个地方。**

### 14.1 为什么一定要改

因为当前实现不是一个“注册式可扩展系统”，而是明确写死了：

- 支持哪些 mimeType
- 图片怎么包装
- PDF 怎么包装
- 预览组件如何渲染
- 上传文案怎么展示

也就是说，现在这套代码更适合：

> 支持少量固定类型，而不是无限扩展类型。

### 14.2 最少要改哪些位置

如果未来要支持更多类型，至少要看这些文件：

- `agent-chat-ui/src/hooks/use-file-upload.tsx`
- `agent-chat-ui/src/lib/multimodal-utils.ts`
- `agent-chat-ui/src/components/thread/MultimodalPreview.tsx`
- `agent-chat-ui/src/components/thread/index.tsx`

### 14.3 如果只是多支持几种“普通文件”

比如想再支持：

- TXT
- CSV
- DOCX

那通常要做：

1. 扩展 `SUPPORTED_FILE_TYPES`
2. 让 `fileToContentBlock()` 能把这些文件统一映射成 `type: file`
3. 让预览组件至少能显示文件名、类型、删除按钮
4. 确认上游 graph 是否认识这种 `file` 块，或者你自己的节点能处理

### 14.4 如果要支持新的模态

比如：

- 音频
- 视频
- 更多专用媒体类型

那就不能只是“多加几个 mimeType”，而是要先决定：

- 新类型在消息里该用什么 block 结构
- UI 预览怎么画
- 上游 graph 如何消费
- 是否需要额外上传存储，而不是继续直接塞 base64

### 14.5 当前方案的长期风险

如果未来支持的类型越来越多，而还继续沿用当前 `if/else` 方式，问题会越来越明显：

- 白名单会越来越长
- 预览逻辑会越来越乱
- 不同类型的元数据结构会越来越分裂
- 前端和 graph 之间的协议会越来越难维护

更合理的长期方向是：

> 把“mimeType -> block builder -> preview renderer -> downstream contract”做成一张注册表，而不是继续堆分支。

---

## 15. 一句话总结

当前 Chat 上传链路的本质是：

> **浏览器本地读取文件 -> 转 base64 -> 封装成多模态消息块 -> 作为 LangGraph run 的 `input.messages` 一部分发给平台。**

其中：

- 图片用 `type: image`
- PDF 用 `type: file`
- 平台层收到的是 JSON + base64 + 元数据
- 平台层本身不做文件解析，只做 run payload 透传

如果未来要支持更多类型，当前代码需要修改，而且最好逐步重构成可注册、可扩展的上传协议层。
