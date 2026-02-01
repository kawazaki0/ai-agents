"""
MCP Client for AI Agents
Connects to the MCP server and provides tool execution capabilities
"""
import json
import os
import subprocess
import threading
from typing import Dict, Optional, Any


class MCPToolClient:
    """Simplified MCP client for tool execution in AI agents"""

    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.request_lock = threading.Lock()
        self._tools_dict: Dict[str, Any] = {}

    def connect(self):
        """Connect to MCP server and discover tools"""
        if not os.path.exists(self.server_script_path):
            raise RuntimeError(f"MCP server script not found: {self.server_script_path}")

        self.process = subprocess.Popen(
            ["python3", self.server_script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )

        init_response = self._send_request({
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "ai-agents-mcp-client", "version": "1.0.0"}
            }
        })

        if "error" in init_response:
            raise RuntimeError(f"Server initialization failed: {init_response['error']}")

        self._send_request({"jsonrpc": "2.0", "method": "notifications/initialized"}, read_stdout=False)

        self._discover_tools()

    def _discover_tools(self):
        """Convert available tools from the server to a dictionary"""
        tools_response = self._send_request({
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/list",
            "params": {}
        })

        if "result" in tools_response and "tools" in tools_response["result"]:
            for tool in tools_response["result"]["tools"]:
                self._tools_dict[tool["name"]] = {
                    "description": tool.get("description", ""),
                    "inputSchema": tool.get("inputSchema", {})
                }

    def get_available_tools_dict(self) -> Dict[str, Any]:
        """Get dictionary of available tools and their schemas"""
        return self._tools_dict.copy()

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name not in self._tools_dict:
            return f"Error: Unknown tool '{tool_name}'. Available tools: {list(self._tools_dict.keys())}"

        try:
            response = self._send_request({
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            })

            if "result" in response:
                # Extract text content from the response
                if "content" in response["result"]:
                    text_parts = []
                    for content_item in response["result"]["content"]:
                        if content_item.get("type") == "text":
                            text_parts.append(content_item.get("text", ""))
                    return "\\n".join(text_parts) if text_parts else "No text content returned"
                else:
                    return str(response["result"])
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                return f"Tool execution error: {error_msg}"

        except Exception as e:
            return f"Tool execution failed: {str(e)}"

    def _get_next_id(self) -> int:
        """Get next request ID in a thread-safe manner"""
        with self.request_lock:
            self.request_id += 1
            return self.request_id

    def _send_request(self, request: Dict[str, Any], read_stdout=True) -> Dict[str, Any]:
        """Send JSON-RPC request and get response"""
        if not self.process:
            raise RuntimeError("No server process active")
        json_str = json.dumps(request) + '\n'
        print("[MCP_CALL]", json_str)
        self.process.stdin.write(json_str)
        self.process.stdin.flush()
        if not read_stdout:
            print("[MCP_NO_STDOUT_RESPONSE]")
            return {}

        response_line = self.process.stdout.readline()
        print("[MCP_RESPONSE]", response_line)

        try:
            return json.loads(response_line.strip())
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON response: {e}")

    def cleanup(self):
        """Clean up resources"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
