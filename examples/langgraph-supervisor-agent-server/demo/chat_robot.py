import os
from typing import Annotated

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

llm = init_chat_model(
    model="deepseek-chat",
    model_provider="deepseek",
    api_key=api_key,
)


class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


# 工具调用
tool = TavilySearch(max_results=2)
tools = [tool]
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)


# def chatbot(state: State):
#     return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph = graph_builder.compile()


from IPython.display import Image, display

try:
    # 1. 首先获取图像的二进制数据
    png_data = graph.get_graph().draw_mermaid_png()

    # 2. 将图像数据保存到文件
    with open("graph_visualization.png", "wb") as f:
        f.write(png_data)
    print("流程图已保存为 graph_visualization.png")

    # 3. 尝试在IPython中显示图像
    display(Image(png_data))
except Exception:
    # This requires some extra dependencies and is optional
    pass


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break
