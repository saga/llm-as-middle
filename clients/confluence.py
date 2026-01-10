import os
import json
import logging
from pydantic import SecretStr
from langchain_core.utils.function_calling import convert_to_openai_function
from ._client_wrapper import ChatOpenAIWrapper

logger = logging.getLogger(__name__)

# LiteLLM proxy作为MCP客户端的桥接
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://litellm-proxy:4000")
LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "dummy-key")
CONFLUENCE_MODEL = os.getenv("CONFLUENCE_MODEL", "confluence-mcp")

# 使用ChatOpenAI（更简洁统一）
llm = ChatOpenAIWrapper(
    model=CONFLUENCE_MODEL,
    api_key=SecretStr(LITELLM_API_KEY),
    base_url=LITELLM_BASE_URL
)

async def search_pages(query: str, limit: int = 10, spaces_filter: str | None = None):
    """
    通过LiteLLM proxy调用Confluence MCP的confluence_search工具
    
    使用ChatOpenAI + tool calling实现，更简洁统一
    """
    try:
        from langchain_core.messages import HumanMessage
        
        # 定义工具schema
        tools = [{
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
        }]
        
        # 使用ChatOpenAI调用，更简洁
        response = await llm.ainvoke(
            [HumanMessage(content=f"Search Confluence: {query}")],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "confluence_search"}}
        )
        
        # 解析响应（LangChain格式）
        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                pass
        
        return []
    except Exception as e:
        logger.error(f"Error searching pages: {e}")
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
    使用ChatOpenAI实现，与其他LLM调用保持一致
    """
    try:
        from langchain_core.messages import HumanMessage
        
        if not page_id and not (title and space_key):
            return {"error": "Either page_id OR both title and space_key must be provided"}
        
        # 定义工具
        tools = [{
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
        }]
        
        response = await llm.ainvoke(
            [HumanMessage(content=f"Get Confluence page: {page_id or title}")],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "confluence_get_page"}}
        )
        
        if hasattr(response, 'content') and response.content:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                return {"content": {"value": response.content}}
        
        return {}
    except Exception as e:
        logger.error