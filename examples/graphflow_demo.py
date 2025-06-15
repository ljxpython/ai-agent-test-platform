"""
参考: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html#creating-and-running-a-flow

"""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import DiGraphBuilder, GraphFlow

from examples.llms import openai_model_client as client

# Create the writer agent
writer = AssistantAgent(
    "writer",
    model_client=client,
    system_message="Draft a short paragraph on climate change.",
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
    system_message="Consolidate the grammar and style edits into a final version.",
)

# Build the workflow graph
builder = DiGraphBuilder()
builder.add_node(writer).add_node(editor1).add_node(editor2).add_node(final_reviewer)

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
)


# Run the workflow
async def main():
    async for i in flow.run_stream(
        task="Write a short paragraph about climate change."
    ):
        print(i)


if __name__ == "__main__":
    asyncio.run(main())
