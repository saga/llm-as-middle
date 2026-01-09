"""LangGraph Agent State定义"""
from typing import TypedDict, Annotated, Sequence
from operator import add


class AgentState(TypedDict):
    """Agent工作流状态"""
    # 用户输入
    user_prompt: str
    
    # 搜索阶段
    search_query: str
    search_results: list[dict]
    page_links: list[str]
    
    # 获取页面阶段
    pages_content: list[dict]
    
    # 存储阶段
    s3_urls: list[str]
    
    # 总结阶段
    summary: str
    final_response: str
    
    # 消息历史（用于LLM调用）
    messages: Annotated[Sequence[dict], add]
    
    # 错误处理
    errors: Annotated[list[str], add]
