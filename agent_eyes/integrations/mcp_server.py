# -*- coding: utf-8 -*-
"""
Agent Eyes MCP Server — expose all capabilities as MCP tools.

Run: python -m agent_eyes.integrations.mcp_server
Or:  agent-eyes serve (after pip install)

10 tools for any MCP-compatible AI Agent.
"""

import asyncio
import json
import sys

from agent_eyes.config import Config
from agent_eyes.core import AgentEyes

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


def create_server():
    """Create and configure the MCP server."""
    if not HAS_MCP:
        print("MCP not installed. Install: pip install agent-eyes[mcp]", file=sys.stderr)
        sys.exit(1)

    server = Server("agent-eyes")
    config = Config()
    eyes = AgentEyes(config)

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="read_url",
                description="Read content from any URL. Supports: web pages, GitHub, Reddit, Twitter, YouTube, Bilibili, WeChat, XiaoHongShu, RSS, Telegram.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to read"},
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="read_batch",
                description="Read multiple URLs concurrently.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {"type": "array", "items": {"type": "string"}, "description": "List of URLs"},
                    },
                    "required": ["urls"],
                },
            ),
            Tool(
                name="detect_platform",
                description="Detect what platform a URL belongs to (github, reddit, twitter, youtube, etc).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to detect"},
                    },
                    "required": ["url"],
                },
            ),
            Tool(
                name="search",
                description="Semantic web search using Exa. Find any information on the internet.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "num_results": {"type": "integer", "description": "Number of results (1-10)", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_reddit",
                description="Search Reddit posts and discussions. Works even when Reddit blocks your IP.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "subreddit": {"type": "string", "description": "Optional subreddit filter (e.g. 'LocalLLaMA')"},
                        "limit": {"type": "integer", "description": "Number of results", "default": 10},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_github",
                description="Search GitHub repositories by topic, keyword, or technology.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "language": {"type": "string", "description": "Filter by language (e.g. 'python')"},
                        "limit": {"type": "integer", "description": "Number of results", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="search_twitter",
                description="Search Twitter/X posts. Uses birdx if available, otherwise Exa.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Number of results", "default": 10},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_status",
                description="Get Agent Eyes status: which platforms are active, which need configuration.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "read_url":
                result = await eyes.read(arguments["url"])
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

            elif name == "read_batch":
                results = await eyes.read_batch(arguments["urls"])
                return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

            elif name == "detect_platform":
                platform = eyes.detect_platform(arguments["url"])
                return [TextContent(type="text", text=f"Platform: {platform}")]

            elif name == "search":
                results = await eyes.search(
                    arguments["query"],
                    num_results=arguments.get("num_results", 5),
                )
                return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

            elif name == "search_reddit":
                results = await eyes.search_reddit(
                    arguments["query"],
                    subreddit=arguments.get("subreddit"),
                    limit=arguments.get("limit", 10),
                )
                return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

            elif name == "search_github":
                results = await eyes.search_github(
                    arguments["query"],
                    language=arguments.get("language"),
                    limit=arguments.get("limit", 5),
                )
                return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

            elif name == "search_twitter":
                results = await eyes.search_twitter(
                    arguments["query"],
                    limit=arguments.get("limit", 10),
                )
                return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

            elif name == "get_status":
                report = eyes.doctor_report()
                return [TextContent(type="text", text=report)]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


async def main():
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
