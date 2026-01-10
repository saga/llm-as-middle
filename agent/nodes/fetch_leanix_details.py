"""Fetch detailed LeanIX fact sheet information"""
import logging
from typing import Any
from clients.leanix import get_fact_sheet
from agent.state import AgentState

logger = logging.getLogger(__name__)


async def fetch_leanix_details_node(state: AgentState) -> dict[str, Any]:
    """Fetch detailed information for LeanIX fact sheets"""
    fact_sheet_ids = state.get('leanix_fact_sheet_ids', [])
    logger.info(f"Fetching details for {len(fact_sheet_ids)} LeanIX fact sheets")
    
    fact_sheets_detail = []
    errors = []
    
    for fs_id in fact_sheet_ids:
        try:
            fs_data = await get_fact_sheet(
                fact_sheet_id=fs_id,
                include_relations=True,
                include_documents=True
            )
            
            if fs_data:
                fact_sheets_detail.append(fs_data)
                logger.info(f"Fetched fact sheet {fs_id}")
            else:
                error_msg = f"Failed to fetch fact sheet {fs_id}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
        except Exception as e:
            error_msg = f"Exception fetching fact sheet {fs_id}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    logger.info(f"Successfully fetched {len(fact_sheets_detail)} fact sheets")
    
    return {
        "leanix_fact_sheets_detail": fact_sheets_detail,
        "errors": errors
    }
