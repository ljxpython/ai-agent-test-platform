"""
参考: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html#creating-and-running-a-flow


Sequential chains  顺序链

Parallel fan-outs  并行分支

Conditional branching  条件分支

Loops with safe exit conditions 带安全退出条件的循环


https://microsoft.github.io/autogen/stable/reference/python/autogen_agentchat.teams.html#autogen_agentchat.teams.DiGraphBuilder

Each node in the graph represents an agent. Edges define execution paths between agents, and can optionally be conditioned on message content using callable functions.
图中的每个节点代表一个代理。边定义了代理之间的执行路径，并且可以选择性地使用可调用函数根据消息内容进行条件控制。



"""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow

from examples.llms import openai_model_client as client


async def create_Sequential_flow():
    # Create the writer agent
    writer = AssistantAgent(
        "writer",
        model_client=client,
        system_message="编写一段关于气候变化的简短文章使用中文",
    )

    # Create the reviewer agent
    reviewer = AssistantAgent(
        "reviewer", model_client=client, system_message="优化文章,增加可阅读性"
    )

    # Build the graph
    builder = DiGraphBuilder()
    builder.add_node(writer).add_node(reviewer)
    builder.add_edge(writer, reviewer)

    # Build and validate the graph
    graph = builder.build()

    # Create the flow
    flow = GraphFlow(
        builder.get_participants(),
        graph=graph,
        termination_condition=MaxMessageTermination(3),
    )
    return flow


async def create_Parallel_flow():
    agent_a = AssistantAgent(
        "A", model_client=client, system_message="You are a helpful assistant."
    )
    agent_b = AssistantAgent(
        "B", model_client=client, system_message="Translate input to Chinese."
    )
    agent_c = AssistantAgent(
        "C", model_client=client, system_message="Translate input to Japanese."
    )

    # Create a directed graph with fan-out flow A -> (B, C).
    builder = DiGraphBuilder()
    builder.add_node(agent_a).add_node(agent_b).add_node(agent_c)
    builder.add_edge(agent_a, agent_b).add_edge(agent_a, agent_c)
    graph = builder.build()

    # Create a GraphFlow team with the directed graph.
    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
        termination_condition=MaxMessageTermination(5),
    )
    return team


async def create_multi_parallel_flow():
    # Create the writer agent
    writer = AssistantAgent(
        "writer",
        model_client=client,
        system_message="撰写一篇剪短的关于气候的文章",
    )

    # Create two editor agents
    editor1 = AssistantAgent(
        "editor1", model_client=client, system_message="Edit the paragraph for grammar."
    )

    editor2 = AssistantAgent(
        "editor2", model_client=client, system_message="Edit the paragraph for style."
    )

    # Create the final reviewer agent
    final_reviewer = AssistantAgent(
        "final_reviewer",
        model_client=client,
        system_message="将语法和风格转化为最终的文章",
    )

    # Build the workflow graph
    builder = DiGraphBuilder()
    builder.add_node(writer).add_node(editor1).add_node(editor2).add_node(
        final_reviewer
    )

    # Fan-out from writer to editor1 and editor2
    builder.add_edge(writer, editor1)
    builder.add_edge(writer, editor2)

    # Fan-in both editors into final reviewer
    builder.add_edge(editor1, final_reviewer)
    builder.add_edge(editor2, final_reviewer)

    # Build and validate the graph
    graph = builder.build()

    # Create the flow
    flow = GraphFlow(
        participants=builder.get_participants(),
        graph=graph,
        termination_condition=MaxMessageTermination(5),
    )
    return flow


# condition
async def create_conditional_flow():
    agent_a = AssistantAgent(
        "A",
        model_client=client,
        system_message="Detect if the input is in Chinese. If it is, say 'yes', else say 'no', and nothing else.",
    )
    agent_b = AssistantAgent(
        "B", model_client=client, system_message="Translate input to English."
    )
    agent_c = AssistantAgent(
        "C", model_client=client, system_message="Translate input to Chinese."
    )

    # Create a directed graph with conditional branching flow A -> B ("yes"), A -> C (otherwise).
    builder = DiGraphBuilder()
    builder.add_node(agent_a).add_node(agent_b).add_node(agent_c)
    # Create conditions as callables that check the message content.
    builder.add_edge(
        agent_a, agent_b, condition=lambda msg: "yes" in msg.to_model_text()
    )
    builder.add_edge(
        agent_a, agent_c, condition=lambda msg: "yes" not in msg.to_model_text()
    )
    graph = builder.build()

    # Create a GraphFlow team with the directed graph.
    team = GraphFlow(
        participants=[agent_a, agent_b, agent_c],
        graph=graph,
        termination_condition=MaxMessageTermination(5),
    )
    return team


# Run the workflow
async def main():
    # async for i in flow.run_stream(

    # flow = await create_Sequential_flow()

    # flow = await create_Parallel_flow()

    # flow = await create_multi_parallel_flow()

    flow = await create_conditional_flow()

    async for i in flow.run_stream(task="写一篇关于气候变化的文章"):
        print(i)


if __name__ == "__main__":
    asyncio.run(main())
