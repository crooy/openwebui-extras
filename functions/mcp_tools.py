"""
@function
type: pipe
name: MCP Tools
description: Integrates with LiteLLM's Model Context Protocol (MCP) to provide access to external tools
version: 0.1.0
repository: https://github.com/openwebui/open-webui
author: Your Name
email: your.email@example.com

@params
mcp_base_url:
    type: string
    description: Base URL for the MCP server
    required: true
    default: http://localhost:4000
mcp_api_key:
    type: string
    description: API key for MCP server authentication
    required: false
name_prefix:
    type: string
    description: Prefix to add to tool names for identification
    required: false
    default: MCP/
"""

import json
from typing import Any, Dict, List

import aiohttp
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        MCP_BASE_URL: str = Field(
            default="http://localhost:4000",
            description="Base URL for the MCP server"
        )
        MCP_API_KEY: str = Field(
            default="",
            description="API key for MCP server authentication"
        )
        NAME_PREFIX: str = Field(
            default="MCP/",
            description="Prefix to add to tool names"
        )

    def __init__(self) -> None:
        self.valves = self.Valves()
        self.tools: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Fetch available tools from MCP server on startup"""
        self.tools = await self._fetch_tools()

    def pipes(self) -> List[Dict[str, str]]:
        """Return list of available MCP tools as models"""
        if not self.tools:
            return [{
                "id": "error",
                "name": f"{self.valves.NAME_PREFIX}No tools available"
            }]

        return [
            {
                "id": tool["name"],
                "name": f"{self.valves.NAME_PREFIX}{tool['name']}"
            }
            for tool in self.tools
        ]

    async def _fetch_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from the MCP server"""
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            if self.valves.MCP_API_KEY:
                headers["Authorization"] = f"Bearer {self.valves.MCP_API_KEY}"

            try:
                async with session.get(
                    f"{self.valves.MCP_BASE_URL}/mcp/tools/list",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch tools: {response.status}")
                    data = await response.json()
                    tools: List[Dict[str, Any]] = data.get("tools", [])
                    return tools
            except Exception as e:
                print(f"Error fetching MCP tools: {e}")
                return []

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call on the MCP server"""
        async with aiohttp.ClientSession() as session:
            headers = {"Content-Type": "application/json"}
            if self.valves.MCP_API_KEY:
                headers["Authorization"] = f"Bearer {self.valves.MCP_API_KEY}"

            try:
                async with session.post(
                    f"{self.valves.MCP_BASE_URL}/mcp/tools/call",
                    headers=headers,
                    json={
                        "name": tool_name,
                        "arguments": arguments
                    }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Tool call failed: {response.status}")
                    result: Dict[str, Any] = await response.json()
                    return result
            except Exception as e:
                print(f"Error calling MCP tool: {e}")
                return {"error": str(e)}

    async def pipe(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Process messages and handle tool calls"""
        messages = body.get("messages", [])
        if not messages:
            return {
                "id": "mcp-response",
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "No messages provided"
                    }
                }]
            }

        # Check last message for tool calls
        last_message = messages[-1]
        response: Dict[str, Any] = {
            "id": "mcp-response",
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": []
                }
            }]
        }

        if last_message.get("tool_calls"):
            tool_results = []
            for tool_call in last_message["tool_calls"]:
                result = await self._call_tool(
                    tool_call["function"]["name"],
                    json.loads(tool_call["function"]["arguments"])
                )
                tool_results.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "content": json.dumps(result)
                })
            response["choices"][0]["message"]["content"] = json.dumps(tool_results)
        else:
            # Return available tools
            response["choices"][0]["message"]["content"] = "MCP Tools are available for use. What would you like to do?"
            response["choices"][0]["message"]["tool_calls"] = [
                {
                    "id": f"tool-{i}",
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                } for i, tool in enumerate(self.tools)
            ]

        return response


# Initialize the pipe function
pipe = Pipe
