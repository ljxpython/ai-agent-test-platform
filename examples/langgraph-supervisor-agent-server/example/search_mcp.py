#!/usr/bin/env python3
"""
简单的搜索MCP服务 - 模拟搜索功能
"""
import asyncio
import json
import sys
from typing import Any, Dict, List


class MockSearchMCPServer:
    """模拟搜索MCP服务器"""

    def __init__(self):
        self.mock_data = {
            "2024年北京GDP": "2024年北京市GDP约为4.37万亿元，同比增长5.2%",
            "2024年上海GDP": "2024年上海市GDP约为4.72万亿元，同比增长5.8%",
            "2024年中国GDP": "2024年中国GDP预计约为126万亿元",
            "beijing gdp 2024": "Beijing GDP in 2024 is approximately 4.37 trillion yuan",
            "shanghai gdp 2024": "Shanghai GDP in 2024 is approximately 4.72 trillion yuan",
            "china gdp 2024": "China GDP in 2024 is approximately 126 trillion yuan",
        }

    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """模拟搜索功能"""
        results = []
        query_lower = query.lower()

        for key, value in self.mock_data.items():
            if any(
                word in key.lower() or word in value.lower()
                for word in query_lower.split()
            ):
                results.append(
                    {
                        "title": f"搜索结果: {key}",
                        "content": value,
                        "url": f"https://example.com/search/{key.replace(' ', '_')}",
                        "snippet": value[:100] + "..." if len(value) > 100 else value,
                    }
                )
                if len(results) >= max_results:
                    break

        if not results:
            results.append(
                {
                    "title": f"关于 '{query}' 的搜索结果",
                    "content": f"找到了关于 {query} 的相关信息，但具体数据需要进一步查证",
                    "url": "https://example.com/search",
                    "snippet": "模拟搜索结果",
                }
            )

        return results

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理MCP请求"""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "search",
                        "description": "Search for information on the web",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query",
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return",
                                    "default": 5,
                                },
                            },
                            "required": ["query"],
                        },
                    }
                ]
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "search":
                query = arguments.get("query", "")
                max_results = arguments.get("max_results", 5)

                search_results = self.search(query, max_results)

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(
                                search_results, ensure_ascii=False, indent=2
                            ),
                        }
                    ]
                }

        return {"error": f"Unknown method: {method}"}


async def main():
    """主函数 - 处理stdio通信"""
    server = MockSearchMCPServer()

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
