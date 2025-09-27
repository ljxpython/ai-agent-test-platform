import operator
from typing import Annotated

from config import llm
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    input_text: str
    processed_text: str
    analysis_result: str
    final_output: str


class SubgraphState(TypedDict):
    text: str
    result: str


def create_text_processing_subgraph():
    """创建文本处理子图"""

    def clean_text(state: SubgraphState):
        """清理文本"""
        text = state["text"]
        # 简单的文本清理
        cleaned = text.strip().lower()
        return {"result": cleaned}

    def validate_text(state: SubgraphState):
        """验证文本"""
        text = state["result"]
        if len(text) > 0:
            return {"result": f"[已验证] {text}"}
        else:
            return {"result": "[错误] 空文本"}

    # 构建子图
    subgraph_builder = StateGraph(SubgraphState)
    subgraph_builder.add_node("clean", clean_text)
    subgraph_builder.add_node("validate", validate_text)

    subgraph_builder.add_edge(START, "clean")
    subgraph_builder.add_edge("clean", "validate")
    subgraph_builder.add_edge("validate", END)

    return subgraph_builder.compile()


def create_analysis_subgraph():
    """创建分析子图"""

    def count_words(state: SubgraphState):
        """统计词数"""
        text = state["text"]
        word_count = len(text.split())
        return {"result": f"词数: {word_count}"}

    def analyze_sentiment(state: SubgraphState):
        """情感分析（简化版）"""
        text = state["text"]
        positive_words = ["好", "棒", "喜欢", "开心"]
        negative_words = ["坏", "差", "讨厌", "生气"]

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        if pos_count > neg_count:
            sentiment = "积极"
        elif neg_count > pos_count:
            sentiment = "消极"
        else:
            sentiment = "中性"

        prev_result = state.get("result", "")
        return {"result": f"{prev_result}, 情感: {sentiment}"}

    # 构建分析子图
    subgraph_builder = StateGraph(SubgraphState)
    subgraph_builder.add_node("count_words", count_words)
    subgraph_builder.add_node("analyze_sentiment", analyze_sentiment)

    subgraph_builder.add_edge(START, "count_words")
    subgraph_builder.add_edge("count_words", "analyze_sentiment")
    subgraph_builder.add_edge("analyze_sentiment", END)

    return subgraph_builder.compile()


# 创建子图实例
text_processor = create_text_processing_subgraph()
text_analyzer = create_analysis_subgraph()


def process_with_subgraph(state: State):
    """使用子图处理文本"""
    input_text = state["input_text"]

    # 调用文本处理子图
    processing_result = text_processor.invoke({"text": input_text})
    processed_text = processing_result["result"]

    return {"processed_text": processed_text}


def analyze_with_subgraph(state: State):
    """使用子图分析文本"""
    processed_text = state["processed_text"]

    # 调用分析子图
    analysis_result = text_analyzer.invoke({"text": processed_text})
    analysis = analysis_result["result"]

    return {"analysis_result": analysis}


def generate_final_output(state: State):
    """生成最终输出"""
    input_text = state["input_text"]
    processed_text = state["processed_text"]
    analysis_result = state["analysis_result"]

    final_output = f"""
文本处理报告：
原始文本: {input_text}
处理后文本: {processed_text}
分析结果: {analysis_result}
"""

    return {"final_output": final_output.strip()}


# 构建主图
main_graph_builder = StateGraph(State)
main_graph_builder.add_node("process", process_with_subgraph)
main_graph_builder.add_node("analyze", analyze_with_subgraph)
main_graph_builder.add_node("output", generate_final_output)

main_graph_builder.add_edge(START, "process")
main_graph_builder.add_edge("process", "analyze")
main_graph_builder.add_edge("analyze", "output")
main_graph_builder.add_edge("output", END)

# 编译主图
main_graph = main_graph_builder.compile()


def run_subgraph_demo():
    """运行子图演示"""
    print("子图演示启动！")
    print("这个演示展示如何使用子图来模块化处理流程。")
    print("输入 'quit' 退出。")

    while True:
        user_input = input("\n请输入要处理的文本: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        try:
            # 运行主图
            result = main_graph.invoke({"input_text": user_input})
            print(result["final_output"])

        except Exception as e:
            print(f"处理错误: {e}")


def demo_subgraph_isolation():
    """演示子图隔离性"""
    print("\n" + "=" * 50)
    print("子图隔离性演示")
    print("=" * 50)

    # 直接测试子图
    print("\n=== 直接测试文本处理子图 ===")
    test_texts = ["  Hello World  ", "PYTHON编程", ""]

    for text in test_texts:
        print(f"输入: '{text}'")
        result = text_processor.invoke({"text": text})
        print(f"输出: '{result['result']}'")

    print("\n=== 直接测试分析子图 ===")
    analysis_texts = ["我很开心今天天气好", "这个产品很差劲", "今天是星期一"]

    for text in analysis_texts:
        print(f"输入: '{text}'")
        result = text_analyzer.invoke({"text": text})
        print(f"输出: '{result['result']}'")


def demo_parallel_subgraphs():
    """演示并行子图处理"""
    print("\n" + "=" * 50)
    print("并行子图处理演示")
    print("=" * 50)

    import asyncio

    async def parallel_process(text):
        """并行处理文本"""

        # 模拟异步调用子图
        async def process_async():
            return text_processor.invoke({"text": text})

        async def analyze_async():
            return text_analyzer.invoke({"text": text})

        # 并行执行
        process_task = asyncio.create_task(process_async())
        analyze_task = asyncio.create_task(analyze_async())

        process_result, analyze_result = await asyncio.gather(
            process_task, analyze_task
        )

        return {
            "processed": process_result["result"],
            "analyzed": analyze_result["result"],
        }

    # 测试并行处理
    test_text = "我喜欢编程，这很有趣！"
    print(f"处理文本: {test_text}")

    try:
        result = asyncio.run(parallel_process(test_text))
        print(f"处理结果: {result['processed']}")
        print(f"分析结果: {result['analyzed']}")
    except Exception as e:
        print(f"并行处理错误: {e}")


def demo_nested_subgraphs():
    """演示嵌套子图"""
    print("\n" + "=" * 50)
    print("嵌套子图演示")
    print("=" * 50)

    # 创建一个包含子图的子图
    class NestedState(TypedDict):
        input_data: str
        stage1_result: str
        stage2_result: str
        final_result: str

    def stage1_with_subgraph(state: NestedState):
        """第一阶段：使用文本处理子图"""
        input_data = state["input_data"]
        result = text_processor.invoke({"text": input_data})
        return {"stage1_result": result["result"]}

    def stage2_with_subgraph(state: NestedState):
        """第二阶段：使用分析子图"""
        stage1_result = state["stage1_result"]
        result = text_analyzer.invoke({"text": stage1_result})
        return {"stage2_result": result["result"]}

    def combine_results(state: NestedState):
        """合并结果"""
        input_data = state["input_data"]
        stage1 = state["stage1_result"]
        stage2 = state["stage2_result"]

        final = f"输入: {input_data} → 处理: {stage1} → 分析: {stage2}"
        return {"final_result": final}

    # 构建嵌套图
    nested_graph = StateGraph(NestedState)
    nested_graph.add_node("stage1", stage1_with_subgraph)
    nested_graph.add_node("stage2", stage2_with_subgraph)
    nested_graph.add_node("combine", combine_results)

    nested_graph.add_edge(START, "stage1")
    nested_graph.add_edge("stage1", "stage2")
    nested_graph.add_edge("stage2", "combine")
    nested_graph.add_edge("combine", END)

    compiled_nested = nested_graph.compile()

    # 测试嵌套图
    test_input = "  我觉得这个项目很棒！  "
    print(f"测试输入: '{test_input}'")

    result = compiled_nested.invoke({"input_data": test_input})
    print(f"最终结果: {result['final_result']}")


if __name__ == "__main__":
    # run_subgraph_demo()
    demo_subgraph_isolation()
    demo_parallel_subgraphs()
    demo_nested_subgraphs()
