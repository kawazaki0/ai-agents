#!/usr/bin/env python3
import json
import logging
import sys
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPServer:
    def __init__(self):
        self.tools = {
            "echo": self.echo_tool,
            "calculate": self.calculate_tool,
            "get_system_info": self.get_system_info_tool,
            "advanced": self.advanced_tool
        }
        self.tool_schemas = {
            "echo": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text message to echo back"}
                },
                "required": ["text"]
            },
            "calculate": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string",
                                   "description": "A mathematical expression to evaluate (e.g., '2 + 3 * 4')"}
                },
                "required": ["expression"]
            },
            "get_system_info": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "advanced": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Person's name"},
                    "age": {"type": "integer", "description": "Person's age in years"},
                    "skills": {"type": "array", "items": {"type": "string"},
                               "description": "List of skills the person has"},
                    "metadata": {"type": "object", "description": "Optional additional metadata dictionary"}
                },
                "required": ["name", "age", "skills"]
            }
        }

    def echo_tool(self, text: str) -> Dict[str, Any]:
        """Simple echo tool that returns the input text.

        text: The text message to echo back
        """
        return {
            "content": [{"type": "text", "text": f"Echo: {text}"}]
        }

    def calculate_tool(self, expression: str) -> Dict[str, Any]:
        """Simple calculator tool that evaluates mathematical expressions.

        expression: A mathematical expression to evaluate (e.g., "2 + 3 * 4")
        """
        try:
            result = eval(expression)
            return {
                "content": [{"type": "text", "text": f"Result: {result}"}]
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}]
            }

    def get_system_info_tool(self) -> Dict[str, Any]:
        """Get basic system information including platform and Python version."""
        import platform
        import os

        info = {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "working_directory": os.getcwd()
        }

        return {
            "content": [{"type": "text", "text": f"System Info: {json.dumps(info, indent=2)}"}]
        }

    def advanced_tool(self, name: str, age: int, skills: List[str], metadata: Optional[Dict[str, Any]] = None) -> Dict[
        str, Any]:
        """Advanced tool demonstrating complex type hints.

        name: Person's name
        age: Person's age in years
        skills: List of skills the person has
        metadata: Optional additional metadata dictionary
        """
        result = {
            "name": name,
            "age": age,
            "skills": skills,
            "skill_count": len(skills)
        }

        if metadata:
            result["metadata"] = metadata

        return {
            "content": [{"type": "text", "text": f"Person Profile: {json.dumps(result, indent=2)}"}]
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""
        # Log incoming request
        print(f"[MCP_REQUEST] {json.dumps(request)}", file=sys.stderr, flush=True)

        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": {
                        "name": "sample-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }

        elif method == "notifications/initialized":
            response = ""
        elif method == "tools/list":
            tools_list = []
            for tool_name, tool_func in self.tools.items():
                input_schema = self.tool_schemas[tool_name]
                description = tool_func.__doc__.split('\n')[0] if tool_func.__doc__ else f"Tool: {tool_name}"
                tool_info = {
                    "name": tool_name,
                    "description": description.strip(),
                    "inputSchema": input_schema
                }
                tools_list.append(tool_info)

            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools_list
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](**arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": result
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -1,
                            "message": f"Tool execution error: {str(e)}"
                        }
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -1,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }

        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -1,
                    "message": f"Unknown method: {method}"
                }
            }

        # Log outgoing response
        print(f"[MCP_RESPONSE] {json.dumps(response)}", file=sys.stderr, flush=True)
        return response

    def run(self):
        """Run the MCP server"""
        logger.info("Starting MCP Server...")

        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break

                try:
                    request = json.loads(line.strip())
                    response = self.handle_request(request)
                    if response:
                        print(json.dumps(response))
                        sys.stdout.flush()
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {line}")
                except Exception as e:
                    logger.error(f"Error processing request: {e}")

        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")


if __name__ == "__main__":
    server = MCPServer()
    server.run()
