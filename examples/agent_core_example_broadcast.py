"""

Autogen 消息机制 + 运行时的使用案例   运行时广播消息,给所有订阅消息的智能体范例



"""

import asyncio
from dataclasses import dataclass

from autogen_core import (
    AgentId,
    MessageContext,
    RoutedAgent,
    TopicId,
    message_handler,
    type_subscription,
)
from pydantic import BaseModel, Field


@dataclass
class MessageA:
    msg: str


# 推荐
class MessageB(BaseModel):
    task: str


@type_subscription(topic_type="topicA")
class ImageAnalyzerAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("图片分析智能体")

    @message_handler
    async def handle_my_message(self, message: MessageB, ctx: MessageContext) -> None:
        print("图片分析已完成")
        print(message.task)

        a = MessageA(msg="图片分析已完成，请开始生成用例")
        # await self.send_message(a, AgentId("agent2", "default"))
        await self.publish_message(a, topic_id=TopicId(type="topicB", source="default"))
        await asyncio.sleep(10)
        print("wait 10s done anaylysis")


@type_subscription(topic_type="topicA")
class TestCaseGeneratorAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("用例生成智能体")

    @message_handler
    async def handle_my_message(self, message: MessageA, ctx: MessageContext) -> None:
        print("用例生成已完成")
        print(message.msg)

    @message_handler
    async def handle_my_message_2(self, message: MessageB, ctx: MessageContext) -> None:
        print("用例生成已完成22")
        print(message.task)
        await asyncio.sleep(10)
        print("wait 10s done testcase")


async def main():
    # 运行时环境
    from autogen_core import SingleThreadedAgentRuntime

    runtime = SingleThreadedAgentRuntime()

    # 注册智能体到运行时环境
    await ImageAnalyzerAgent.register(runtime, "agent1", lambda: ImageAnalyzerAgent())
    await TestCaseGeneratorAgent.register(
        runtime, "agent2", lambda: TestCaseGeneratorAgent()
    )
    runtime.start()
    b = MessageB(task="开始分析图片")
    # 直接发送消息给 图片分析智能体
    # await runtime.send_message(b, AgentId("agent1", "default"))
    # await runtime.send_message(b, AgentId("agent2", "default"))

    # 通过广播发送消息给所有订阅了 topicA 的智能体
    await runtime.publish_message(b, topic_id=TopicId(type="topicA", source="default"))
    await runtime.stop_when_idle()


asyncio.run(main())
