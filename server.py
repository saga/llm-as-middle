from mcp.server.fastmcp import FastMCP
from clients.confluence import search_pages, get_page
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP("enterprise-doc-agent")

@mcp.tool()
async def confluence_search(query: str, limit: int = 10, spaces_filter: str | None = None):
    """
    Search Confluence content using simple terms or CQL.
    
    查询可以是简单文本（如'项目文档'）或CQL查询字符串。
    简单查询默认使用'siteSearch'，如果不支持会自动回退到'text'搜索。
    
    CQL示例：
    - 基本搜索: 'type=page AND space=DEV'
    - 按标题搜索: 'title~"会议记录"'
    - 使用siteSearch: 'siteSearch ~ "重要概念"'
    - 使用text搜索: 'text ~ "重要概念"'
    - 最近内容: 'created >= "2023-01-01"'
    - 带标签的内容: 'label=documentation'
    
    Args:
        query: Search query - 简单文本或CQL查询字符串
        limit: Maximum number of results (1-50, 默认10)
        spaces_filter: 可选，逗号分隔的space keys用于过滤结果
    
    Returns:
        List of simplified Confluence page objects with metadata
    """
    pages = await search_pages(query, limit, spaces_filter)
    return pages

@mcp.tool()
async def confluence_get_page(
    page_id: str | None = None,
    title: str | None = None,
    space_key: str | None = None,
    include_metadata: bool = True,
    convert_to_markdown: bool = True
):
    """
    Get Confluence page content.
    
    可以通过page_id或者(title + space_key)组合来获取页面。
    如果提供了page_id，title和space_key将被忽略。
    
    Args:
        page_id: Confluence页面ID（可从URL中获取）
        title: 页面的精确标题（必须与space_key一起使用）
        space_key: Space的key（必须与title一起使用）
        include_metadata: 是否包含页面元数据（默认True）
        convert_to_markdown: 转换内容为markdown(True)或保持HTML(False)，默认True
    
    Returns:
        Page object with content and/or metadata
    """
    page = await get_page(
        page_id=page_id,
        title=title,
        space_key=space_key,
        include_metadata=include_metadata,
        convert_to_markdown=convert_to_markdown
    )
    return page

# 添加健康检查路由
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """健康检查端点"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "enterprise-doc-agent"}
    )
