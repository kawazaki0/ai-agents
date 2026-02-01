import json
from typing import Callable

from mcp_client import MCPToolClient


class AgentTools:
    def __init__(self, config):
        self._mcp_tools_dict = None
        self._config = config
        self._mcp_client = None

    def init(self):
        if not self._mcp_client:
            self._mcp_client = MCPToolClient(self._config.mcp_server_path)
            self._mcp_client.connect()
            self._mcp_tools_dict = self._mcp_client.get_available_tools_dict()
            print(f"[SYSTEM] Connected to MCP server with tools: {list(self._mcp_tools_dict.keys())}")

    def get_tool(self, tool_name: str) -> Callable | None:
        if not self._mcp_client:
            raise RuntimeError("MCP client not initialized. Call init() first.")
        if tool_name not in self._mcp_tools_dict:
            return None
        def mcp_tool_wrapper(tool_input: str) -> str:
            return self._mcp_client.call_tool(tool_name, json.loads(tool_input))
        mcp_tool_wrapper.__name__ = f"mcp_{tool_name}"
        return mcp_tool_wrapper

    def get_available_tools(self):
        return self._mcp_tools_dict

    def cleanup(self):
        if self._mcp_client:
            self._mcp_client.cleanup()
