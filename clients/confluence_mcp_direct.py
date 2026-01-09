"""
备用实现：直接使用MCP客户端连接Confluence MCP Server

如果不使用LiteLLM proxy，可以用这个实现替换clients/confluence.py

使用方法：
1. 在pyproject.toml中确保有mcp依赖
2. 将此文件内容复制到clients/confluence.py
3. 设置环境变量CONFLUENCE_MCP_URL

基于 sooperset/mcp-atlassian 实现
"""

import os
import json
from mcp import ClientSession
from mcp.client.sse import sse_client

CONFLUENCE_MCP_URL = os.getenv("CONFLUENCE_MCP_URL", "http://confluence-mcp:8080/sse")

async def search_pages(query: str, limit: int = 10, spaces_filter: str | None = None):
    """直接通过MCP客户端调用Confluence MCP的confluence_search工具"""
    try:
        async with sse_client(CONFLUENCE_MCP_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 构建参数
                args = {"query": query, "limit": limit}
                if spaces_filter:
                    args["spaces_filter"] = spaces_filter
                
                # 调用工具（工具名是confluence_search）
                result = await session.call_tool("confluence_search", args)
                
                # result.content是工具返回的JSON字符串
                if hasattr(result, 'content') and result.content:
                    # 解析JSON
                    if isinstance(result.content, str):
                        return json.loads(result.content)
                    return result.content
                return []
    except Exception as e:
        print(f"Error searching pages via MCP: {e}")
        return []

async def get_page(
    page_id: str | None = None,
    title: str | None = None,
    space_key: str | None = None,
    include_metadata: bool = True,
    convert_to_markdown: bool = True
):
    """直接通过MCP客户端调用Confluence MCP的confluence_get_page工具"""
    try:
        async with sse_client(CONFLUENCE_MCP_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 构建参数
                args = {
                    "include_metadata": include_metadata,
                    "convert_to_markdown": convert_to_markdown
                }
                
                if page_id:
                    args["page_id"] = str(page_id)
                elif title and space_key:
                    args["title"] = title
                    args["space_key"] = space_key
                else:
                    return {"error": "Either page_id OR both title and space_key must be provided"}
                
                # 调用工具（工具名是confluence_get_page）
                result = await session.call_tool("confluence_get_page", args)
                
                # result.content是工具返回的JSON字符串
                if hasattr(result, 'content') and result.content:
                    if isinstance(result.content, str):
                        return json.loads(result.content)
                    return result.content
                return {}
    except Exception as e:
        print(f"Error getting page via MCP: {e}")
        return {"error": str(e)}
