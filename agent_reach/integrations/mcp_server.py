# -*- coding: utf-8 -*-
"""
Agent Reach MCP Server — expose all capabilities as MCP tools.

Run: python -m agent_reach.integrations.mcp_server

8 tools for any MCP-compatible AI Agent.
"""

import asyncio
import json
import sys

from agent_reach.config import Config
from agent_reach.core import AgentReach

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


def create_server():
    if not HAS_MCP:
        print("MCP not installed. Install: pip install agent-reach[mcp]", file=sys.stderr)
        sys.exit(1)

    server = Server("agent-reach")
    config = Config()
    eyes = AgentReach(config)

    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="read_url",
                 description="Read content from any URL. Supports: web, GitHub, Reddit, Twitter, YouTube, Bilibili, RSS.",
                 inputSchema={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}),
            Tool(name="read_batch",
                 description="Read multiple URLs concurrently.",
                 inputSchema={"type": "object", "properties": {"urls": {"type": "array", "items": {"type": "string"}}}, "required": ["urls"]}),
            Tool(name="detect_platform",
                 description="Detect what platform a URL belongs to.",
                 inputSchema={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}),
            Tool(name="search",
                 description="Semantic web search via Exa.",
                 inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "num_results": {"type": "integer", "default": 5}}, "required": ["query"]}),
            Tool(name="search_reddit",
                 description="Search Reddit posts.",
                 inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "subreddit": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}),
            Tool(name="search_github",
                 description="Search GitHub repositories.",
                 inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "language": {"type": "string"}, "limit": {"type": "integer", "default": 5}}, "required": ["query"]}),
            Tool(name="search_twitter",
                 description="Search Twitter/X posts.",
                 inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, "required": ["query"]}),
            Tool(name="get_status",
                 description="Get Agent Reach status: which channels are active.",
                 inputSchema={"type": "object", "properties": {}}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "read_url":
                result = await eyes.read(arguments["url"])
            elif name == "read_batch":
                result = await eyes.read_batch(arguments["urls"])
            elif name == "detect_platform":
                result = eyes.detect_platform(arguments["url"])
            elif name == "search":
                result = await eyes.search(arguments["query"], arguments.get("num_results", 5))
            elif name == "search_reddit":
                result = await eyes.search_reddit(arguments["query"], arguments.get("subreddit"), arguments.get("limit", 10))
            elif name == "search_github":
                result = await eyes.search_github(arguments["query"], arguments.get("language"), arguments.get("limit", 5))
            elif name == "search_twitter":
                result = await eyes.search_twitter(arguments["query"], arguments.get("limit", 10))
            elif name == "get_status":
                result = eyes.doctor_report()
            else:
                result = f"Unknown tool: {name}"

            text = json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else str(result)
            return [TextContent(type="text", text=text)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


async def main():
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
