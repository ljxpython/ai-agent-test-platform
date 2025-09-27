#!/usr/bin/env python3
"""
简单的图表生成MCP服务 - 模拟图表生成功能
"""
import asyncio
import json
import os
import sys
from typing import Any, Dict


class MockChartMCPServer:
    """模拟图表生成MCP服务器"""

    def __init__(self):
        self.chart_counter = 0

    def create_chart(
        self, chart_type: str, data: Dict[str, Any], title: str = ""
    ) -> Dict[str, Any]:
        """模拟创建图表"""
        self.chart_counter += 1

        # 模拟生成图表文件
        filename = f"chart_{self.chart_counter}_{chart_type}.png"
        filepath = os.path.join("/tmp", filename)

        # 创建一个简单的文本文件作为模拟图表
        chart_content = f"""
图表类型: {chart_type}
标题: {title}
数据: {json.dumps(data, ensure_ascii=False, indent=2)}
生成时间: {asyncio.get_event_loop().time()}
图表编号: {self.chart_counter}
"""

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(chart_content)
        except:
            filepath = f"mock_chart_{self.chart_counter}.txt"

        return {
            "chart_id": f"chart_{self.chart_counter}",
            "chart_type": chart_type,
            "title": title,
            "file_path": filepath,
            "status": "created",
            "data_points": len(data) if isinstance(data, (list, dict)) else 1,
            "message": f"成功创建{chart_type}图表: {title}",
        }

    def create_bar_chart(
        self, data: Dict[str, float], title: str = "Bar Chart"
    ) -> Dict[str, Any]:
        """创建柱状图"""
        return self.create_chart("bar", data, title)

    def create_pie_chart(
        self, data: Dict[str, float], title: str = "Pie Chart"
    ) -> Dict[str, Any]:
        """创建饼图"""
        return self.create_chart("pie", data, title)

    def create_line_chart(
        self, data: Dict[str, float], title: str = "Line Chart"
    ) -> Dict[str, Any]:
        """创建折线图"""
        return self.create_chart("line", data, title)

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "create_bar_chart",
                        "description": "Create a bar chart from data",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "data": {
                                    "type": "object",
                                    "description": "Data for the chart (key-value pairs)",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Chart title",
                                    "default": "Bar Chart",
                                },
                            },
                            "required": ["data"],
                        },
                    },
                    {
                        "name": "create_pie_chart",
                        "description": "Create a pie chart from data",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "data": {
                                    "type": "object",
                                    "description": "Data for the chart (key-value pairs)",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Chart title",
                                    "default": "Pie Chart",
                                },
                            },
                            "required": ["data"],
                        },
                    },
                    {
                        "name": "create_line_chart",
                        "description": "Create a line chart from data",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "data": {
                                    "type": "object",
                                    "description": "Data for the chart (key-value pairs)",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Chart title",
                                    "default": "Line Chart",
                                },
                            },
                            "required": ["data"],
                        },
                    },
                    {
                        "name": "create_chart",
                        "description": "Create a chart of specified type",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "chart_type": {
                                    "type": "string",
                                    "description": "Type of chart (bar, pie, line)",
                                    "enum": ["bar", "pie", "line"],
                                },
                                "data": {
                                    "type": "object",
                                    "description": "Data for the chart",
                                },
                                "title": {
                                    "type": "string",
                                    "description": "Chart title",
                                    "default": "Chart",
                                },
                            },
                            "required": ["chart_type", "data"],
                        },
                    },
                ]
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "create_bar_chart":
                data = arguments.get("data", {})
                title = arguments.get("title", "Bar Chart")
                result = self.create_bar_chart(data, title)

            elif tool_name == "create_pie_chart":
                data = arguments.get("data", {})
                title = arguments.get("title", "Pie Chart")
                result = self.create_pie_chart(data, title)

            elif tool_name == "create_line_chart":
                data = arguments.get("data", {})
                title = arguments.get("title", "Line Chart")
                result = self.create_line_chart(data, title)

            elif tool_name == "create_chart":
                chart_type = arguments.get("chart_type", "bar")
                data = arguments.get("data", {})
                title = arguments.get("title", "Chart")
                result = self.create_chart(chart_type, data, title)

            else:
                return {"error": f"Unknown tool: {tool_name}"}

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2),
                    }
                ]
            }

        return {"error": f"Unknown method: {method}"}


async def main():
    """主函数 - 处理stdio通信"""
    server = MockChartMCPServer()

    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            if not line:
                break

            request = json.loads(line.strip())
            response = await server.handle_request(request)

            # 添加请求ID
            if "id" in request:
                response["id"] = request["id"]

            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except EOFError:
            break
        except Exception as e:
            error_response = {
                "error": str(e),
                "id": request.get("id") if "request" in locals() else None,
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())
