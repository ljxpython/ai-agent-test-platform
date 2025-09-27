"""
自定义 MCP 服务器示例
这个示例展示如何创建一个简单的 MCP 服务器
"""

import json
import sys
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]


class SimpleMCPServer:
    """简单的 MCP 服务器实现"""

    def __init__(self):
        self.tools = {
            "calculator": Tool(
                name="calculator",
                description="执行基本数学计算",
                input_schema={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 '2 + 3 * 4'",
                        }
                    },
                    "required": ["expression"],
                },
            ),
            "text_analyzer": Tool(
                name="text_analyzer",
                description="分析文本的基本属性",
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "要分析的文本"}
                    },
                    "required": ["text"],
                },
            ),
            "file_manager": Tool(
                name="file_manager",
                description="简单的文件管理操作",
                input_schema={
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "list"],
                            "description": "文件操作类型",
                        },
                        "filename": {"type": "string", "description": "文件名"},
                        "content": {
                            "type": "string",
                            "description": "写入的内容（仅用于写操作）",
                        },
                    },
                    "required": ["operation"],
                },
            ),
        }

        # 模拟文件系统
        self.file_system = {
            "config.txt": "# 配置文件\napi_key=test123\nport=8080",
            "data.csv": "name,age,city\n张三,25,北京\n李四,30,上海",
            "notes.txt": "这是一个笔记文件",
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in self.tools.values()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定工具"""
        if name == "calculator":
            return self._calculator(arguments)
        elif name == "text_analyzer":
            return self._text_analyzer(arguments)
        elif name == "file_manager":
            return self._file_manager(arguments)
        else:
            return {"error": f"未知工具: {name}"}

    def _calculator(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """计算器工具实现"""
        try:
            expression = args.get("expression", "")

            # 安全的数学计算
            allowed_chars = set("0123456789+-*/().")
            if not all(c in allowed_chars or c.isspace() for c in expression):
                return {"error": "表达式包含不允许的字符"}

            result = eval(expression)
            return {"content": [{"type": "text", "text": f"{expression} = {result}"}]}
        except Exception as e:
            return {"error": f"计算错误: {e}"}

    def _text_analyzer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """文本分析工具实现"""
        try:
            text = args.get("text", "")

            # 基本文本分析
            word_count = len(text.split())
            char_count = len(text)
            line_count = len(text.split("\n"))

            # 简单情感分析
            positive_words = ["好", "棒", "喜欢", "开心", "满意"]
            negative_words = ["坏", "差", "讨厌", "生气", "不满"]

            pos_count = sum(1 for word in positive_words if word in text)
            neg_count = sum(1 for word in negative_words if word in text)

            if pos_count > neg_count:
                sentiment = "积极"
            elif neg_count > pos_count:
                sentiment = "消极"
            else:
                sentiment = "中性"

            analysis = f"""
文本分析结果：
- 字符数：{char_count}
- 词数：{word_count}
- 行数：{line_count}
- 情感倾向：{sentiment}
"""

            return {"content": [{"type": "text", "text": analysis.strip()}]}
        except Exception as e:
            return {"error": f"分析错误: {e}"}

    def _file_manager(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """文件管理工具实现"""
        try:
            operation = args.get("operation")
            filename = args.get("filename", "")
            content = args.get("content", "")

            if operation == "list":
                files = list(self.file_system.keys())
                return {
                    "content": [
                        {"type": "text", "text": f"可用文件: {', '.join(files)}"}
                    ]
                }

            elif operation == "read":
                if filename in self.file_system:
                    file_content = self.file_system[filename]
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"文件 {filename} 内容:\n{file_content}",
                            }
                        ]
                    }
                else:
                    return {"error": f"文件 {filename} 不存在"}

            elif operation == "write":
                if not filename:
                    return {"error": "写操作需要指定文件名"}

                self.file_system[filename] = content
                return {"content": [{"type": "text", "text": f"已写入文件 {filename}"}]}

            else:
                return {"error": f"不支持的操作: {operation}"}

        except Exception as e:
            return {"error": f"文件操作错误: {e}"}

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {"tools": self.list_tools()}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            return self.call_tool(tool_name, arguments)
        else:
            return {"error": f"未知方法: {method}"}


def run_mcp_server():
    """运行 MCP 服务器"""
    server = SimpleMCPServer()

    print("简单 MCP 服务器启动！", file=sys.stderr)
    print("支持的工具:", file=sys.stderr)
    for tool in server.list_tools():
        print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)

    # 处理标准输入的请求
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({"error": "无效的 JSON"}))
        except Exception as e:
            print(json.dumps({"error": f"服务器错误: {e}"}))


def test_mcp_server():
    """测试 MCP 服务器"""
    print("测试自定义 MCP 服务器")
    print("=" * 50)

    server = SimpleMCPServer()

    # 测试列出工具
    print("\n1. 列出工具:")
    tools_response = server.handle_request({"method": "tools/list"})
    for tool in tools_response["tools"]:
        print(f"  - {tool['name']}: {tool['description']}")

    # 测试计算器工具
    print("\n2. 测试计算器:")
    calc_tests = ["2 + 3", "10 * 5 + 2", "(8 - 3) * 4"]
    for expr in calc_tests:
        response = server.handle_request(
            {
                "method": "tools/call",
                "params": {"name": "calculator", "arguments": {"expression": expr}},
            }
        )
        if "error" in response:
            print(f"  {expr} -> 错误: {response['error']}")
        else:
            print(f"  {expr} -> {response['content'][0]['text']}")

    # 测试文本分析工具
    print("\n3. 测试文本分析:")
    text_tests = ["这是一个好的例子", "我很讨厌这个坏的结果", "今天天气不错，心情很好"]
    for text in text_tests:
        response = server.handle_request(
            {
                "method": "tools/call",
                "params": {"name": "text_analyzer", "arguments": {"text": text}},
            }
        )
        if "error" in response:
            print(f"  错误: {response['error']}")
        else:
            print(f"  文本: {text}")
            print(f"  分析: {response['content'][0]['text']}")
            print()

    # 测试文件管理工具
    print("\n4. 测试文件管理:")

    # 列出文件
    response = server.handle_request(
        {
            "method": "tools/call",
            "params": {"name": "file_manager", "arguments": {"operation": "list"}},
        }
    )
    print(f"  {response['content'][0]['text']}")

    # 读取文件
    response = server.handle_request(
        {
            "method": "tools/call",
            "params": {
                "name": "file_manager",
                "arguments": {"operation": "read", "filename": "config.txt"},
            },
        }
    )
    print(f"  {response['content'][0]['text']}")

    # 写入文件
    response = server.handle_request(
        {
            "method": "tools/call",
            "params": {
                "name": "file_manager",
                "arguments": {
                    "operation": "write",
                    "filename": "test.txt",
                    "content": "这是测试内容",
                },
            },
        }
    )
    print(f"  {response['content'][0]['text']}")


def demo_mcp_protocol():
    """演示 MCP 协议"""
    print("\n" + "=" * 50)
    print("MCP 协议演示")
    print("=" * 50)

    server = SimpleMCPServer()

    # 模拟客户端请求
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "calculator", "arguments": {"expression": "5 * 6"}},
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "text_analyzer",
                "arguments": {"text": "LangGraph 是一个很棒的框架"},
            },
        },
    ]

    print("模拟 MCP 客户端-服务器通信:")
    for i, request in enumerate(requests, 1):
        print(f"\n--- 请求 {i} ---")
        print(f"客户端发送: {json.dumps(request, ensure_ascii=False, indent=2)}")

        response = server.handle_request(request)
        response["jsonrpc"] = "2.0"
        response["id"] = request["id"]

        print(f"服务器回复: {json.dumps(response, ensure_ascii=False, indent=2)}")


def demo_mcp_error_handling():
    """演示 MCP 错误处理"""
    print("\n" + "=" * 50)
    print("MCP 错误处理演示")
    print("=" * 50)

    server = SimpleMCPServer()

    # 测试各种错误情况
    error_cases = [
        {"name": "未知方法", "request": {"method": "unknown/method"}},
        {
            "name": "未知工具",
            "request": {
                "method": "tools/call",
                "params": {"name": "unknown_tool", "arguments": {}},
            },
        },
        {
            "name": "无效表达式",
            "request": {
                "method": "tools/call",
                "params": {
                    "name": "calculator",
                    "arguments": {"expression": "invalid expression"},
                },
            },
        },
        {
            "name": "缺少参数",
            "request": {
                "method": "tools/call",
                "params": {"name": "text_analyzer", "arguments": {}},
            },
        },
    ]

    for case in error_cases:
        print(f"\n测试: {case['name']}")
        response = server.handle_request(case["request"])
        if "error" in response:
            print(f"  错误: {response['error']}")
        else:
            print(f"  意外成功: {response}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_mcp_server()
    else:
        test_mcp_server()
        demo_mcp_protocol()
        demo_mcp_error_handling()
