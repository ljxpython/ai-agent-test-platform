"""

封装运行时,使用queue进行消息的传递


"""

import asyncio
import random
import time
from asyncio import Queue
from dataclasses import dataclass
from typing import Any, Optional

import aiofiles
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import (
    ModelClientStreamingChunkEvent,
    TextMessage,
    UserInputRequestedEvent,
)
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import (
    CancellationToken,
    ClosureAgent,
    ClosureContext,
    DefaultTopicId,
    MessageContext,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    message_handler,
    type_subscription,
)
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel, Field
from sympy import content

from examples.document_service import DocumentService
from examples.llms import openai_model_client

app = FastAPI(title="ChatGPT API", version="1.0.0", description="ChatGPT API")

"""
编写一首七言绝句诗（智能体1），
有一个智能体进行评价（智能体2），
评价后发送给用户，用户提出意见（user_proxy），
根据意见优化古诗(智能体3)
，直到同意（终止条件）

过程中将每次的结果进行收集，写入到一个data.txt的文本中（收集结果智能体）

"""
# user_collect_messages = dict[str, asyncio.Queue]
message_queues: dict[str, Queue] = {}  # 按用户ID隔离队列
user_feedback_messages: dict[str, asyncio.Queue] = {}


async def get_feedback_queue(user_id):
    if user_id in user_feedback_messages:
        return user_feedback_messages[user_id]
    else:
        queue = asyncio.Queue()
        user_feedback_messages[user_id] = queue
    return queue


# 放入用户反馈
async def put_feedback(user_id, message):
    queue = await get_feedback_queue(user_id)
    await queue.put(message)


# 获取用户反馈
async def get_feedback(user_id):
    queue = await get_feedback_queue(user_id)
    return await queue.get()


# 定义topic_type
write_story_topic_type = "write_story"
review_story_topic_type = "review_story"
change_story_topic_type = "change_story"


# 定义消息数据类型
class WriteStory(BaseModel):
    user_id: str = Field(..., description="用户ID")
    user_req: str = Field(..., description="用户编写古诗的需求")


class ReviewStory(BaseModel):
    user_id: str = Field(..., description="用户ID")
    # task:str = Field(...,description="评审古诗的标准")
    content: str = Field(..., description="古诗的内容")


class ChangeStory(BaseModel):
    task: str = Field(..., description="修改古诗的要求")


# 定义智能体及标注其订阅的消息类型


@type_subscription(topic_type=write_story_topic_type)
class WriteStoryAgent(RoutedAgent):

    def __init__(self, description):
        super().__init__(description=description)
        self._prompt = """
        你是一位非常闷骚的诗人，写的古诗非常通俗易懂且幽默风趣
        """

    @message_handler
    async def message(self, message: WriteStory, ctx: MessageContext) -> None:
        logger.info(f"开始写诗")

        story_agent = AssistantAgent(
            "story",
            model_client=openai_model_client,
            system_message="你是一名闷骚的极具才华的诗人，可以为用户编写出脍炙人口的诗句来",
        )

        # 新增：定义符合 UserProxyAgent 要求的 input_func（捕获当前消息的 user_id）
        async def user_feedback_input_func(
            prompt: str,  # 必须保留的 prompt 参数（尽管当前场景可能不需要使用）
            cancellation_token: Optional[CancellationToken],  # 必须保留的取消令牌参数
        ) -> str:
            logger.info(f"等待用户反馈")
            # 调用 get_feedback 获取当前用户的反馈（使用 message.user_id）
            return await get_feedback(message.user_id)

        user_feedback = UserProxyAgent(
            "user_approve", description="用户反馈", input_func=user_feedback_input_func
        )

        team = RoundRobinGroupChat(
            [story_agent, user_feedback],
            termination_condition=TextMentionTermination("同意"),
        )
        async for i in team.run_stream(task=message.user_req):
            print(i)

        # 发送给消息收集体
        await self.publish_message(
            message=TaskResponse(
                content="内容很好",
                agent="write_agent",
            ),
            topic_id=TopicId(type=TASK_RESULTS_TOPIC_TYPE, source=self.id.key),
        )

        # 发送给下一个智能体
        await self.publish_message(
            message=ReviewStory(user_id=message.user_id, content="内容很好"),
            topic_id=TopicId(type=review_story_topic_type, source=self.id.key),
        )


@type_subscription(topic_type=review_story_topic_type)
class ReviewAgent(RoutedAgent):

    def __init__(self, description):
        super().__init__(description=description)
        self._prompt = """
        你是一位古诗鉴赏大师，具有批判性思维，可以给古诗提出建设性的修改意见,当收到用户的古诗活，先点评古诗之后给出修改后的古诗
        """

    @message_handler
    async def handle_message(self, message: ReviewStory, ctx: MessageContext) -> None:
        logger.info(message.model_dump())
        # 发送给消息智能体
        await self.publish_message(
            message=TaskResponse(
                content="评审的很好",
                agent="review_agent",
            ),
            topic_id=TopicId(type=TASK_RESULTS_TOPIC_TYPE, source=self.id.key),
        )
        await message_queues[message.user_id].put("CLOSE")


# 消息收集中的智能体
CLOSURE_AGENT_TYPE = "collect_result_agent"
TASK_RESULTS_TOPIC_TYPE = "task-results"


class TaskResponse(BaseModel):
    content: str = Field(..., description="智能体返回的内容")
    agent: str = Field(..., description="智能体名称")


async def collect_result(
    _agent: ClosureContext, message: TaskResponse, ctx: MessageContext
) -> None:
    async with aiofiles.open(file="data.txt", mode="a+", encoding="utf-8") as f:
        await f.write(f"agent:{message.agent}\n")
        await f.write(f"content:{message.content}\n")


class StartRuntime(object):

    def __init__(self):
        self.user_runtimes = {}
        self.user_memerys = {}
        # self.user_collect_messages = dict[str, asyncio.Queue]
        # self.user_feedback_messages = dict[str, asyncio.Queue]

    # user创建运行时
    async def create_user_runtime(self, user_id):
        if user_id in self.user_runtimes:
            return self.user_runtimes[user_id]
        else:
            runtime = SingleThreadedAgentRuntime()
            self.user_runtimes[user_id] = runtime
        return runtime

    # 运行时初始化注册
    async def init_runtime(self, runtime):
        await WriteStoryAgent.register(
            runtime,
            write_story_topic_type,
            lambda: WriteStoryAgent(description="诗歌智能体"),
        )
        await ReviewAgent.register(
            runtime,
            review_story_topic_type,
            lambda: ReviewAgent(description="诗歌评审智能体"),
        )

        # 收集消息智能体
        async def collect_message(
            _agent: ClosureContext, message: TaskResponse, ctx: MessageContext
        ) -> None:
            logger.info(f"消息收集: {message.model_dump()}")

        await ClosureAgent.register_closure(
            runtime,
            CLOSURE_AGENT_TYPE,
            collect_message,
            subscriptions=lambda: [
                TypeSubscription(
                    topic_type=TASK_RESULTS_TOPIC_TYPE, agent_type=CLOSURE_AGENT_TYPE
                )
            ],
        )

    # 发布消息
    async def _publish_message(self, runtime, message: WriteStory):
        await runtime.publish_message(
            message, topic_id=DefaultTopicId(type=write_story_topic_type)
        )
        await runtime.stop_when_idle()
        await runtime.close()

    async def main(self, user_id: str, message: str):
        runtime = await self.create_user_runtime(user_id=user_id)
        runtime.start()
        message_queues[user_id] = asyncio.Queue()
        await self.init_runtime(runtime)
        await self._publish_message(
            runtime, WriteStory(user_id=user_id, user_req=message)
        )


startruntime = StartRuntime()
document_service = DocumentService()


@app.get("/")
async def root():
    return {"message": "Hello World"}


def get_queue(user_id: str) -> Queue:
    if user_id not in message_queues:
        message_queues[user_id] = Queue(maxsize=100)  # 防止内存溢出
    return message_queues[user_id]


# 生产者（AutoGen消息处理）
async def process_autogen_message(user_id: str, msg: str):
    queue = get_queue(user_id)
    await queue.put(f"[Agent] {msg}")  # 非阻塞写入


# 消费者（SSE流生成）
async def message_generator(user_id: str):
    queue = get_queue(user_id)
    try:
        while True:
            message = await queue.get()  # 阻塞直到有消息
            if message == "CLOSE":
                break
            yield f"data: {message}\n\n"
            queue.task_done()  # 标记任务完成
    finally:
        message_queues.pop(user_id, None)  # 清理资源


## sse流式输出
@app.get("/chat")
async def chat(user_id: str, message: str):
    asyncio.create_task(startruntime.main(user_id, message))
    return StreamingResponse(
        message_generator(user_id=user_id),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


@app.get("/feedback")
async def feedback(user_id: str, message: str):

    asyncio.create_task(put_feedback(user_id, message))
    return {"message": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form("default")):
    """文件上传接口 - 使用marker进行高质量文档处理"""
    try:
        print(f"📁 文件上传: {file.filename}, Session ID: {session_id}")
        result = await document_service.save_and_extract_file(file, session_id)
        print(f"✅ 上传成功: 文件ID {result['file_id']} 已关联到 session {session_id}")
        return {"status": "success", "message": "文件上传成功", "data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


if __name__ == "__main__":
    # asyncio.run(start_runtime())
    # start_runtime = StartRuntime()
    # asyncio.run(start_runtime.main())
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
