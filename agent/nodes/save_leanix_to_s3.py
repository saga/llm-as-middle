"""Save LeanIX fact sheets to S3"""
import json
import logging
from datetime import datetime
from typing import Any
from agent.state import AgentState
from ._shared import get_s3_client, get_s3_bucket

logger = logging.getLogger(__name__)


async def save_leanix_to_s3_node(state: AgentState) -> dict[str, Any]:
    """Save LeanIX fact sheets to S3"""
    fact_sheets = state.get('leanix_fact_sheets_detail', [])
    logger.info(f"Saving {len(fact_sheets)} LeanIX fact sheets to S3")
    
    s3_client = get_s3_client()
    s3_bucket = get_s3_bucket()
    s3_urls = []
    errors = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for idx, fs in enumerate(fact_sheets):
        try:
            fs_id = fs.get('id', f'factsheet_{idx}')
            name = fs.get('name', fs.get('displayName', 'Untitled'))
            fs_type = fs.get('type', 'Unknown')
            
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            s3_key = f"leanix-factsheets/{timestamp}/{fs_type}/{fs_id}_{safe_name}.json"
            
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=json.dumps(fs, ensure_ascii=False, indent=2),
                ContentType='application/json',
                Metadata={
                    'factsheet-id': str(fs_id),
                    'name': name,
                    'type': fs_type,
                    'timestamp': timestamp
                }
            )
            
            s3_url = f"s3://{s3_bucket}/{s3_key}"
            s3_urls.append(s3_url)
            logger.info(f"Saved fact sheet {fs_id} to {s3_url}")
            
        except Exception as e:
            error_msg = f"Failed to save fact sheet to S3: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    logger.info(f"Saved {len(s3_urls)} fact sheets to S3")
    
    return {
        "leanix_s3_urls": s3_urls,
        "errors": errors
    }
