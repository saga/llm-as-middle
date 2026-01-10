"""Search LeanIX fact sheets"""
import os
import logging
from typing import Any
from clients.leanix import search_fact_sheets
from agent.state import AgentState

logger = logging.getLogger(__name__)


async def search_leanix_node(state: AgentState) -> dict[str, Any]:
    """Search LeanIX fact sheets based on user query"""
    logger.info(f"Searching LeanIX with query: {state.get('search_query', state['user_prompt'])}")
    
    try:
        search_term = state.get('search_query', state['user_prompt'])
        
        # Simple type detection based on keywords
        fact_sheet_type = None
        query_lower = search_term.lower()
        
        type_keywords = {
            "Application": ["application", "app", "software", "system"],
            "DataObject": ["data", "database", "dataset"],
            "ITComponent": ["component", "infrastructure", "server", "hardware"],
            "BusinessCapability": ["capability", "capabilities", "business capability"],
            "Process": ["process", "workflow", "procedure"],
            "UserGroup": ["user", "team", "group", "stakeholder"],
            "Project": ["project", "initiative"],
            "Interface": ["interface", "api", "integration"],
        }
        
        for fs_type, keywords in type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                fact_sheet_type = fs_type
                break
        
        results = await search_fact_sheets(
            search_term=search_term,
            fact_sheet_type=fact_sheet_type,
            limit=int(os.getenv("SEARCH_LIMIT", "10")),
            include_fields=["tags", "updatedAt"]
        )
        
        logger.info(f"Found {len(results)} fact sheets in LeanIX")
        
        fact_sheet_ids = [fs['id'] for fs in results if fs.get('id')]
        
        return {
            "leanix_results": results,
            "leanix_fact_sheet_ids": fact_sheet_ids,
            "leanix_search_type": fact_sheet_type or "All Types"
        }
    except Exception as e:
        logger.error(f"Error in search_leanix_node: {e}")
        return {
            "leanix_results": [],
            "leanix_fact_sheet_ids": [],
            "errors": [f"LeanIX search failed: {str(e)}"]
        }
