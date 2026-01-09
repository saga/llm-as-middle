from mcp.client import ClientSession
from mcp.client.sse import sse_client

CONFLUENCE_MCP_URL = "http://confluence-mcp:8080/sse"

async def search_pages(query: str, limit: int):
    async with sse_client(CONFLUENCE_MCP_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "search",
                {"query": query, "limit": limit}
            )
            return result.content

async def get_page(page_id: str):
    async with sse_client(CONFLUENCE_MCP_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_page",
                {"id": page_id}
            )
            return result.content
