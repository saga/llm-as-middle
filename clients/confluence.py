import os
import json
from openai import AsyncOpenAI

# LiteLLM proxy作为MCP客户端的桥接
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://litellm-proxy:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "dummy-key")
CONFLUENCE_MODEL = os.getenv("CONFLUENCE_MODEL", "confluence-mcp")

# 初始化OpenAI客户端，指向LiteLLM proxy
client = AsyncOpenAI(
    base_url=LITELLM_BASE_URL,
    api_key=LITELLM_API_KEY
)

async def search_pages(query: str, limit: int = 10, spaces_filter: str | None = None):
    """
    通过LiteLLM proxy调用Confluence MCP的confluence_search工具
    
    根据sooperset/mcp-atlassian实现：
    - 工具名：confluence_search
    - 参数：query (str), limit (int, 默认10), spaces_filter (str | None)
    - 返回：JSON string representing a list of simplified page objects
    
    简化的页面对象包含：
    {
      "id": "页面ID",
      "title": "页面标题",
      "type": "page",
      "url": "页面URL",
      "space": {"key": "SPACE", "name": "Space名称"},
      "author": "作者名",
      "created": "创建时间",
      "updated": "更新时间",
      "content": {"value": "内容", "format": "markdown/storage"}
    }
    """
    try:
        # 构建工具调用参数
        tool_args = {"query": query, "limit": limit}
        if spaces_filter:
            tool_args["spaces_filter"] = spaces_filter
        
        # 使用OpenAI SDK调用（假设LiteLLM已配置MCP工具转发）
        response = await client.chat.completions.create(
            model=CONFLUENCE_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Search Confluence: {query}"
                }
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "confluence_search",
                        "description": "Search Confluence content",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "limit": {"type": "integer", "default": 10},
                                "spaces_filter": {"type": "string"}
                            },
                            "required": ["query"]
                        }
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "confluence_search"}}
        )
        
        # 解析响应
        if response.choices[0].message.tool_calls:
            # 如果LiteLLM返回工具执行结果
            result_content = response.choices[0].message.content
            if result_content:
                try:
                    return json.loads(result_content)
                except json.JSONDecodeError:
                    pass
        
        # 如果没有tool_calls，尝试解析content
        content = response.choices[0].message.content
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 返回空列表
                return []
        
        return []
    except Exception as e:
        print(f"Error searching pages: {e}")
        return []

async def get_page(
    page_id: str | None = None,
    title: str | None = None,
    space_key: str | None = None,
    include_metadata: bool = True,
    convert_to_markdown: bool = True
):
    """
    通过LiteLLM proxy调用Confluence MCP的confluence_get_page工具
    
    根据sooperset/mcp-atlassian实现：
    - 工具名：confluence_get_page
    - 参数：
      * page_id (str | None)
      * title (str | None)
      * space_key (str | None)
      * include_metadata (bool, 默认True)
      * convert_to_markdown (bool, 默认True)
    - 返回：JSON string with page content and/or metadata
    
    返回格式：
    如果include_metadata=True:
      {"metadata": {"id": ..., "title": ..., "content": {...}, ...}}
    否则:
      {"content": {"value": "..."}}
    """
    try:
        # 构建工具参数
        tool_args = {
            "include_metadata": include_metadata,
            "convert_to_markdown": convert_to_markdown
        }
        
        if page_id:
            tool_args["page_id"] = page_id
        elif title and space_key:
            tool_args["title"] = title
            tool_args["space_key"] = space_key
        else:
            return {"error": "Either page_id OR both title and space_key must be provided"}
        
        # 调用LiteLLM
        response = await client.chat.completions.create(
            model=CONFLUENCE_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Get Confluence page: {page_id or title}"
                }
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "confluence_get_page",
                        "description": "Get Confluence page content",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "page_id": {"type": "string"},
                                "title": {"type": "string"},
                                "space_key": {"type": "string"},
                                "include_metadata": {"type": "boolean", "default": True},
                                "convert_to_markdown": {"type": "boolean", "default": True}
                            }
                        }
                    }
                }
            ],
            tool_choice={"type": "function", "function": {"name": "confluence_get_page"}}
        )
        
        # 解析响应
        content = response.choices[0].message.content
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"content": {"value": content}}
        
        return {}
    except Exception as e:
        print(f"Error getting page: {e}")
        return {"error": str(e)}
