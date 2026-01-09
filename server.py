from mcp.server.fastmcp import FastMCP
from clients.confluence import search_pages, get_page

mcp = FastMCP("enterprise-doc-agent")

@mcp.tool()
async def search_confluence(query: str, limit: int = 5):
    """
    Search Confluence pages related to a query.
    """
    pages = await search_pages(query, limit)
    return [
        {
            "id": p["id"],
            "title": p["title"],
            "url": p["url"]
        }
        for p in pages
    ]

@mcp.tool()
async def get_confluence_page(page_id: str):
    """
    Get Confluence page content by page ID.
    """
    page = await get_page(page_id)
    return {
        "title": page["title"],
        "content": page["content"]
    }
