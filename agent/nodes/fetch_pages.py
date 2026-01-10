"""Fetch full content of Confluence pages"""
import logging
from typing import Any
from clients.confluence import get_page
from agent.state import AgentState

logger = logging.getLogger(__name__)


async def fetch_pages_node(state: AgentState) -> dict[str, Any]:
    """Node 3: Fetch page content"""
    logger.info(f"Fetching {len(state['page_links'])} pages")
    
    pages_content = []
    errors = []
    
    for page_id in state['page_links']:
        try:
            page_data = await get_page(
                page_id=page_id,
                include_metadata=True,
                convert_to_markdown=True
            )
            
            if page_data and not page_data.get('error'):
                pages_content.append(page_data)
                logger.info(f"Fetched page {page_id}")
            else:
                error_msg = f"Failed to fetch page {page_id}: {page_data.get('error', 'Unknown error')}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
        except Exception as e:
            error_msg = f"Exception fetching page {page_id}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    logger.info(f"Successfully fetched {len(pages_content)} pages")
    
    return {
        "pages_content": pages_content,
        "errors": errors
    }
