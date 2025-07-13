## 本期内容

利用周末我想继续优化UI测试相关的功能开发,主要想完成以下功能的开发



功能:

- 可以实现对不同项目的ui元素及文本管理,RAG召回,测试用例生成,测试脚本执行及维护

- 图片批量解析且展示
- 支持对上传的图片生成测试用例: backend/app/api/v1/endpoints/web/image_description_generation.py
- 支持将图片+RAG知识库结合生成测试脚本
- playwright执行且展示
- 前端富文本markdown展示测试用例且可以展示编辑



- 图片元素 ,文档可选, 用户需求(可选) ->RAG -> 生成测试用例 -> 用户编辑后 -> 生成脚本-> 执行 -> 展示结果
- 用例支持重新生成



- 生成测试用例一栏,支持选中已经解析的图片->之后图片生成测试用例 -> 用户编辑 -> 生成测试脚本
- 测试脚本可视化-> 可编辑,可执行





- 用户上传图片,不使用sse流式输出
- 生成测试用例,使用sse流式输出,支持选择多个页面元素生成测试用例及RAG文本知识库
-





## UI的分析加入RAG知识库



步骤是

上传图片 -> UI分析

用户自然语言直接完成脚本



```
请仔细阅读backend/services/ui_testing 服务
对之前的业务逻辑进行调整
之前的逻辑: 用户上传图片 给到UIAnalysisAgent分析
用户自然语言描述 给到 InteractionAnalysisAgent分析
最后,汇总给MidsceneGenerationAgent生成测试用例给到ScriptGenerationAgent生成测试脚本,
当前需要结合RAG进行优化,RAG相关服务的核心代码在backend/rag_core中,请仔细阅读
修改逻辑为: 用户上传图片 给到UIAnalysisAgent分析的结果给到 RAG入库
用户直接说明需求 给到 RAG知识库做增强查询 最后将结果 汇总给MidsceneGenerationAgent生成测试用例 汇总后给到 ScriptGenerationAgent生成测试脚本
前端增加对应的上传图片页面及进度查询和相关Collection管理的界面,可以复用backend/api/v1/rag及backend/services/rag中内容

UI前端Collection分为两个,业务element 业务file


v1目录下建立一个ui-test的目录,UI测试相关图标放到该内容下


@ui_testing_router.get("/analysis-progress/{conversation_id}", summary="查询UI分析进度")的处理方式参考backend/api/v1/testcase.py中@testcase_router.post("/generate/streaming")接口的处理方式,使用消息队列来收集和输出消息




```



```
v1目录下建立一个ui-test的目录,UI测试相关图标放到该内容下
```







```
系统管理中,增加项目管理模块,增加前端页面后端接口数据库
用途: 将不同项目的UI,接口测试RAG知识库区分开来,默认设置一个通用项目
```



## 增加项目管理界面



```
前端问题修复:侧边导航栏,当折叠的二级标题全部展开时,侧边栏最下面的基于Autogen 0.5.7的字样会影响二级标题的展示,最下方的二级标题不能看见,修复该问题
```





```
系统管理中,增加项目管理模块,增加前端页面后端接口数据库
用途: 将不同项目的UI,接口测试RAG知识库区分开来,默认设置一个通用项目
```



```
后端/api/v1/system/projects?page=1&page_size=20 请求前端正常接收,但是前端未正常展示
```





```
1. 项目管理界面,设为默认的选项取消
2.前端: 项目管理每一个项目可以折叠,折叠打开可以看到项目所属部分,成员等等这些信息,数据库也增加相应的字段,都是选填,非必填
```



## 数据库迁移支持动态切换

```
数据库的配置参数在backend/conf/settings.yaml中,backend/conf/config.py中使用python的Dynaconf进行管理,我现在想将数据库由sqlite迁移为MySQL,数据库的管理使用Tortoise和aerich,数据库的初始化文件在backend/api_core/database.py中,未来可以支持动态切换数据库,可以支持sqlite,MySQL等,使用backend/conf/settings.yaml可以进行动态切换和迁移,完成上述功能
```









## RAG系统优化

```
1. 将embedding_model替换为,bge-m3,dimension为1024	,embedding_model和dimension是绑定在一起的,bge-m3的dimension为1024
2. 删除当前创建的collection,重新创建,嵌入模型修改为bge-m3
3. 当新建collection时,有一个默认的配置,当什么都不指定时默认        dimension:为当前模型对应的dimension
        top_k: 5
        similarity_threshold: 0.7
        chunk_size: 1000
        chunk_overlap: 200
4. 修改受到影响的相关代码及数据库,可能有一下几个 backend/rag_core  backend/services/rag   backend/services/ui_testing
```

理解的很到位

![image-20250628094415822](./assets/image-20250628094415822.png)





```
仔细阅读backend/rag_core  backend/api/v1/chat.py backend/services/ragbackend/services/ai_chat/autogen_service.py  backend/api/v1/rag/documents.py
1. RAG知识库增加一个更新的功能,点击更新后,可以将向量数据库中的collection详细信息读取出来,然后和当前数据库中的信息做校对,修改数据库中记录的错误信息 backend/services/rag
2. /api/v1/rag/documents/9的删除报错
3. 调用/api/v1/chat/upload 提示,文档重复,但是我已经调用/api/v1/rag/documents/9进行删除了,预期应该是可以再次上传
```





## 图片上传与RAG知识库对接



{project}_ui_element

{project}_document

和AI对话如下:

1. 接口功能实现: sse流式输出 + 实时更新更新状态+返回解析的结果+ 嵌入向量数据库的的结果

2. 接口参数: project , 图片文件, conversation_id

3. 上传图片的逻辑:

检查project是否存在,如果不存在,在projects数据库中创建一个对应的project,相关逻辑可以参考backend/api/v1/projects.py中的使用

检查collection是否存在:会根据project创建两个collection :名称如下:{project}_ui_element

{project}_document

检查是否为图片格式: 如果不是,报错返回

如果为图片格式检查该图片是否上传到对应的collection中,使用MD5验证,查询rag_file_records中是否有相同的MD5

如果md5不同,代表为上传过该图片,进入智能体解析图片的服务:

解析图片的逻辑为:  backend/services/ui_testing/agents.py中调用UIAnalysisAgent对图片进行解析,将解析的结果传入到对应的RAG知识库中,在这过程中,实时输出智能体输出的结果及传入RAG知识库的状态,更新数据库中的状态

4. RAG相关

```
请仔细阅读RAG知识库的封装框架及使用说明和步骤,代码及说明在backend/rag_core中,应用范例:接口层:backend/api/v1/testcase.py,服务层:backend/services/rag
阅读完backend/rag_core相关文档和范例后,进行开发
优先从backend/rag_core找可以复用的代码
```

4. 智能体的开发:

请仔细熟悉我的智能体发开框架及步骤,代码及说明在backend/ai_core中,应用范例:接口层:backend/api/v1/testcase.py,服务层:backend/services/testcase

5. 整个过程使用消息队列+sse流式输出的方式,代码参考

```
消息队列复用backend/ai_core/message_queue.py中的代码
服务层的代码可以查看backend/services/testcase/agents.py中的队列消息使用
尽可能的复用backend/ai_core/message_queue.py代码中已有的功能
范例:
 # 构建队列消息
 from backend.ai_core.message_queue import put_message_to_queue

queue_message = {
    "type": "streaming_chunk",
    "source": "需求分析智能体",
    "content": item.content,
    "message_type": "streaming",
    "timestamp": datetime.now().isoformat(),
}

logger.debug(f"   🏗️ 构建队列消息: {queue_message}")
try:
    # 序列化消息
    serialized_message = json.dumps(
        queue_message, ensure_ascii=False
    )
 await put_message_to_queue(
                                conversation_id, serialized_message
                            )
# API层写法
 # 启动后台任务处理智能体流程 - 参考examples/topic1.py
    logger.info(f"🚀 [API-流式生成-队列模式] 启动后台任务 | 对话ID: {conversation_id}")
    asyncio.create_task(testcase_service.start_streaming_generation(requirement))
# 返回队列消费者的流式响应 - 直接使用message_queue的SSE函数
logger.info(
    f"📡 [API-流式生成-队列模式] 返回队列消费者流式响应 | 对话ID: {conversation_id}"
)
# 直接使用message_queue的SSE流式函数
from backend.ai_core.message_queue import get_streaming_sse_messages_from_queue

return StreamingResponse(
    get_streaming_sse_messages_from_queue(conversation_id),
    media_type="text/plain",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
    },
)

```

6. RAG知识库相关



6. API相关的开发和设计:

请仔细阅读backend/docs的内容,熟悉后端开发的设计和规范



7. 要有详细的log输出

8. 尽量复用各个core中写好的功能,避免重复造轮子



上传参数 project 文件



上述内容完成后,AI处理

```
✅ 核心功能实现
SSE流式输出: 实时返回处理状态和智能体分析结果
实时状态更新: 每个处理步骤都有详细的状态反馈
返回解析结果: 智能体分析结果通过消息队列实时输出
嵌入向量数据库: 分析结果自动存储到RAG知识库
✅ 接口参数支持
project: 项目名称（必填）
图片文件: 支持多种图片格式
conversation_id: 对话ID（可选，自动生成）
✅ 完整上传逻辑
项目检查: 自动创建不存在的项目
Collection检查: 自动创建 {project}_ui_element 和 {project}_document
图片格式验证: 严格验证支持的图片格式
MD5重复检测: 基于MD5+Collection的精确重复检测
智能体解析: 集成完整的UIAnalysisAgent四智能体协作分析
RAG存储: 分析结果自动存储到对应的RAG知识库
📁 创建的文件
backend/api/v1/ui_test/upload.py - API接口层
backend/services/ui_testing/upload_service.py - 服务层
backend/schemas/ui_test.py - Schema定义
test_ui_upload_api.py - 完整API测试脚本
demo_ui_upload.py - 功能演示脚本
UI_IMAGE_UPLOAD_IMPLEMENTATION.md - 详细实现文档
IMPLEMENTATION_SUMMARY.md - 总结文档
```





接下来优化

1. 支持多个图片同时上传
2. 也支持后台运行

继续和AI进行对话

```
1. 请按照AI智能体系统的开发规范来进行开发,相关资料阅读backend/ai_core文件夹,具体修改,services层分agents,runtime和业务service分别为backend/services/ui_testing/agents.py backend/services/ui_testing/ui_runtime.py backend/services/ui_testing/ui_service.py 在如上三个文件内进行开发,将backend/services/ui_testing/upload_service.py代码移植到对应的代码中
2. 上传文件支持多个图片同时上传,去除上传图片中格式格式不符合(格式检查),已经上传的图片(md5检查)
3. 后台任务:支持后台查询每一个图片的解析进程,使用数据库来维护,每个图片处理的都是一个子任务,后端把实时的结果不断更新到该数据库,用户这样就可以在前端调用接口来查询后台解析的进展了,设计适合的数据库
```



```
在frontend/src/pages中创建一个ui-test的目录,设计你认为适合的美观大气的前端,完成图片上传解析,任务查询这两个需求
```



```
1. ui-test内存放ui测试相关的功能模块,去除之前的midscene智能机,ui测试脚本生成,UI界面分析,ui测试智能助手页面
2. 刚才生成的文件frontend/src/pages/ui-test/components frontend/src/pages/ui-test/types frontend/src/pages/ui-test/utils 都整合到frontend/src目录下,将刚才的页面放到一级目录UI测试目录下展示
```



```
1. backend/api/v1/ui_test/upload.py中接口进行修改,ui_upload_router.post("/upload/images/streaming")修改接口名,上传图片的功能不使用流式输出,而是直接将状态存储到数据库中,将相关的代码中,使用队列消息的地方去掉
2. backend/services/ui_testing/agents.py中UIImageUploadAgent做的事情,我认为不属于智能体做的事情,应该放到ui_service.py,当做业务前置处理
```



```
1.不需要消息队列的方式吧内容流式输出,需要吧每个图片的处理流程记录到数据库中,有相应的接口查询所有任务的状态可以放在前端展示,比如 backend/services/ui_testing/agents.py中handle_ui_analysi 中put_message_to_queue 就应该替换成存储到数据库中
2. backend/api/v1/ui_test/upload.py查看是否有查询所有图片处理状态的接口,如果没有则添加,支持根据项目和图片和任务id查询
3. python中所有方法和类的导入不要在函数内部导入,直接放在代码的开头导入
```



```
对图片的分析需要使用多模态,代码参考官网:https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/messages.html 该功能比较常用,看下可否将该功能封装的更加通用一些放入backend/ai_core/llm.py或者backend/ai_core/factory.py中,让业务使用的更加方便
业务层只需要导入就可以使用,不需要上层再次封装
增加健壮性和容错机制,且每一步都有日志记录,之后检查可能受到影响的业务代码,将其修正
```





## 问题



```
RAG封装后,数据库让AI写个文件告诉用户怎么使用
后端目录下的docs应该存放整体的框架开发流程而非接口开发流程,让AI重新生成
```
