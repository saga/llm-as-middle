"""Search Confluence for relevant pages"""
import os
import logging
from typing import Any
from clients.confluence import search_pages
from agent.state import AgentState

logger = logging.getLogger(__name__)


async def search_confluence_node(state: AgentState) -> dict[str, Any]:
    """Node 2: Search Confluence"""
    logger.info(f"Searching Confluence with query: {state['search_query']}")
    
    try:
        results = await search_pages(
            query=state['search_query'],
            limit=int(os.getenv("SEARCH_LIMIT", "10"))
        )
        
        page_links = []
        for page in results:
            if isinstance(page, dict) and page.get('id'):
                page_links.append(page['id'])
        
        logger.info(f"Found {len(page_links)} pages")
        
        return {
            "search_results": results,
            "page_links": page_links
        }
    except Exception as e:
        logger.error(f"Error in search_confluence_node: {e}")
        return {
            "search_results": [],
            "page_links": [],
            "errors": [f"Confluence search failed: {str(e)}"]
        }
