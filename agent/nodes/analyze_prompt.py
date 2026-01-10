"""Analyze user prompt and generate search query"""
import logging
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState
from ._shared import SearchQuery, get_llm

logger = logging.getLogger(__name__)


async def analyze_prompt_node(state: AgentState) -> dict[str, Any]:
    """Node 1: Analyze user prompt and generate search query"""
    logger.info(f"Analyzing user prompt: {state['user_prompt']}")
    
    try:
        llm = get_llm()
        structured_llm = llm.with_structured_output(SearchQuery)
        
        system_msg = SystemMessage(content="""
You are a Confluence search assistant. Based on the user's question, generate the most appropriate Confluence CQL search query.

Rules:
- If the user's question contains specific keywords, use text ~ "keyword" or siteSearch ~ "keyword"
- If recent content is needed, add time filter: lastModified > startOfMonth("-1M")
- If user specified a space, add: space = "SPACE_KEY"
- Keep the query concise and effective
        """)
        
        human_msg = HumanMessage(content=f"User question: {state['user_prompt']}")
        result = await structured_llm.ainvoke([system_msg, human_msg])  # type: ignore
        
        logger.info(f"Generated search query: {result['query']} (reasoning: {result['reasoning']})")
        
        return {
            "search_query": result['query'],
            "messages": [human_msg]
        }
    except Exception as e:
        logger.error(f"Error in analyze_prompt_node: {e}")
        return {
            "search_query": f'text ~ "{state["user_prompt"]}"',
            "errors": [f"Prompt analysis failed: {str(e)}"]
        }
