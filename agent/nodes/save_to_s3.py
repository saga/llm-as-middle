"""Save Confluence pages to S3"""
import json
import logging
from datetime import datetime
from typing import Any
from agent.state import AgentState
from ._shared import get_s3_client, get_s3_bucket

logger = logging.getLogger(__name__)


async def save_to_s3_node(state: AgentState) -> dict[str, Any]:
    """Node 4: Save content to S3"""
    logger.info(f"Saving {len(state['pages_content'])} pages to S3")
    
    s3_client = get_s3_client()
    s3_bucket = get_s3_bucket()
    s3_urls = []
    errors = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for idx, page in enumerate(state['pages_content']):
        try:
            metadata = page.get('metadata', {})
            page_id = metadata.get('id', f'page_{idx}')
            title = metadata.get('title', 'Untitled')
            
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            s3_key = f"confluence-docs/{timestamp}/{page_id}_{safe_title}.json"
            
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=json.dumps(page, ensure_ascii=False, indent=2),
                ContentType='application/json',
                Metadata={
                    'page-id': str(page_id),
                    'title': title,
                    'timestamp': timestamp
                }
            )
            
            s3_url = f"s3://{s3_bucket}/{s3_key}"
            s3_urls.append(s3_url)
            logger.info(f"Saved page {page_id} to {s3_url}")
            
        except Exception as e:
            error_msg = f"Failed to save page to S3: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    logger.info(f"Saved {len(s3_urls)} pages to S3")
    
    return {
        "s3_urls": s3_urls,
        "errors": errors
    }
