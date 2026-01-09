"""LangGraph Agent State definition"""
from typing import TypedDict, Annotated, Sequence
from operator import add


class AgentState(TypedDict):
    """Agent workflow state"""
    # User input
    user_prompt: str
    system_prompt: str
    
    # Search phase
    search_query: str
    search_results: list[dict]
    page_links: list[str]
    
    # Fetch pages phase
    pages_content: list[dict]
    
    # Storage phase
    s3_urls: list[str]
    
    # Summarization phase
    summary: str
    final_response: str
    
    # Message history (for LLM calls)
    messages: Annotated[Sequence[dict], add]
    
    # Error handling
    errors: Annotated[list[str], add]
