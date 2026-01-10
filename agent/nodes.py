"""LangGraph Agent node definitions"""
import os
import json
import logging
from datetime import datetime
from typing import Any, Optional
import boto3
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from clients.confluence import search_pages, get_page
from clients.leanix import (
    search_fact_sheets,
    get_fact_sheet,
    search_applications,
    get_fact_sheet_types
)
from auth import get_access_token
from .state import AgentState

logger = logging.getLogger(__name__)


# Pydantic model definitions
class SearchQuery(BaseModel):
    """Confluence search query structure"""
    query: str = Field(description="CQL search query string")
    reasoning: str = Field(description="Brief explanation of why this query was generated")


class DocumentSummary(BaseModel):
    """Document summary structure"""
    answer: str = Field(description="Direct answer to user's question")
    key_points: list[str] = Field(description="Key points extracted from documents")
    references: list[dict[str, str]] = Field(description="Referenced documents with title and url")

# Initialize LLM - using MSAL token
def get_llm():
    """Get LLM instance configured with MSAL authentication"""
    # Get Azure AD access token
    access_token = get_access_token()
    
    from pydantic import SecretStr
    
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "gpt-4"),
        temperature=0.7,
        api_key=SecretStr(access_token),  # Use MSAL token as API key
        base_url=os.getenv("LITELLM_BASE_URL", "http://localhost:4000"),
        default_headers={"Authorization": f"Bearer {access_token}"}
    )

# Initialize LLM
llm = get_llm()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)
S3_BUCKET = os.getenv("S3_BUCKET", "confluence-docs-backup")


async def analyze_prompt_node(state: AgentState) -> dict[str, Any]:
    """Node 1: Analyze user prompt and generate search query"""
    logger.info(f"Analyzing user prompt: {state['user_prompt']}")
    
    try:
        # Generate search query using structured output
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
            "search_query": f'text ~ "{state["user_prompt"]}"',  # Fallback to simple query
            "errors": [f"Prompt analysis failed: {str(e)}"]
        }


async def search_confluence_node(state: AgentState) -> dict[str, Any]:
    """Node 2: Search Confluence"""
    logger.info(f"Searching Confluence with query: {state['search_query']}")
    
    try:
        # Search Confluence
        results = await search_pages(
            query=state['search_query'],
            limit=int(os.getenv("SEARCH_LIMIT", "10"))
        )
        
        # Extract page links
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


async def fetch_pages_node(state: AgentState) -> dict[str, Any]:
    """Node 3: Fetch page content"""
    logger.info(f"Fetching {len(state['page_links'])} pages")
    
    pages_content = []
    errors = []
    
    for page_id in state['page_links']:
        try:
            # Fetch page content
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


async def save_to_s3_node(state: AgentState) -> dict[str, Any]:
    """Node 4: Save content to S3"""
    logger.info(f"Saving {len(state['pages_content'])} pages to S3")
    
    s3_urls = []
    errors = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for idx, page in enumerate(state['pages_content']):
        try:
            # Extract page metadata
            metadata = page.get('metadata', {})
            page_id = metadata.get('id', f'page_{idx}')
            title = metadata.get('title', 'Untitled')
            
            # Build S3 key
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            s3_key = f"confluence-docs/{timestamp}/{page_id}_{safe_title}.json"
            
            # Upload to S3
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=json.dumps(page, ensure_ascii=False, indent=2),
                ContentType='application/json',
                Metadata={
                    'page-id': str(page_id),
                    'title': title,
                    'timestamp': timestamp
                }
            )
            
            s3_url = f"s3://{S3_BUCKET}/{s3_key}"
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


async def summarize_node(state: AgentState) -> dict[str, Any]:
    """Node 5: Summarize page content and generate final response"""
    logger.info("Summarizing pages and generating final response")
    
    try:
        # Prepare page content summary
        pages_summary = []
        for page in state['pages_content']:
            metadata = page.get('metadata', {})
            content_data = metadata.get('content', {})
            
            pages_summary.append({
                'title': metadata.get('title', 'Untitled'),
                'url': metadata.get('url', ''),
                'content_preview': content_data.get('value', '')[:500]  # First 500 characters
            })
        
        # Generate summary using structured output
        structured_llm = llm.with_structured_output(DocumentSummary)
        
        # Build system message with optional custom system prompt
        base_system_content = """You are a Confluence documentation assistant. Based on the user's question and the retrieved Confluence pages, provide accurate and helpful answers.

Requirements:
1. Answer the user's question directly
2. Extract key points
3. Record the source of referenced documents
4. If page content doesn't fully match the question, mention this
5. Keep the answer concise and clear"""
        
        if state.get('system_prompt'):
            system_content = f"{state['system_prompt']}\n\n{base_system_content}"
        else:
            system_content = base_system_content
        
        system_msg = SystemMessage(content=system_content)
        
        user_content = f"""
User question: {state['user_prompt']}

Retrieved Confluence pages (total: {len(pages_summary)}):

"""
        for i, page in enumerate(pages_summary, 1):
            user_content += f"""
{i}. [{page['title']}]
   URL: {page['url']}
   Content preview: {page['content_preview']}...

"""
        
        human_msg = HumanMessage(content=user_content)
        
        # Call LLM to generate structured summary
        result = await structured_llm.ainvoke([system_msg, human_msg])  # type: ignore
        
        # Build final response
        final_response = f"""{result['answer']}

**Key Points:**
"""
        for i, point in enumerate(result['key_points'], 1):
            final_response += f"{i}. {point}\n"
        
        final_response += "\n**Referenced Documents:**\n"
        for ref in result['references']:
            final_response += f"- [{ref['title']}]({ref['url']})\n"
        
        final_response += "\n---\n📚 Related documents saved to S3:\n"
        for url in state['s3_urls']:
            final_response += f"- {url}\n"
        
        if state.get('errors'):
            final_response += f"\n⚠️ Warning: {len(state['errors'])} error(s) occurred during processing, some content may be incomplete."
        
        logger.info("Summary generated successfully")
        
        return {
            "summary": result['answer'],
            "final_response": final_response,
            "messages": [human_msg]
        }
        
    except Exception as e:
        error_msg = f"Summarization failed: {str(e)}"
        logger.error(error_msg)
        return {
            "summary": "Failed to generate summary",
            "final_response": f"Sorry, unable to generate summary. Error: {str(e)}",
            "errors": [error_msg]
        }


# LeanIX-specific nodes

async def search_leanix_node(state: AgentState) -> dict[str, Any]:
    """
    Search LeanIX fact sheets based on user query
    
    Searches for fact sheets (Applications, DataObjects, ITComponents, etc.)
    using the LeanIX GraphQL API
    """
    logger.info(f"Searching LeanIX with query: {state.get('search_query', state['user_prompt'])}")
    
    try:
        # Extract search parameters from user prompt
        search_term = state.get('search_query', state['user_prompt'])
        
        # Determine if user is looking for a specific fact sheet type
        fact_sheet_type = None
        query_lower = search_term.lower()
        
        # Simple type detection based on keywords
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
        
        # Search fact sheets
        results = await search_fact_sheets(
            search_term=search_term,
            fact_sheet_type=fact_sheet_type,
            limit=int(os.getenv("SEARCH_LIMIT", "10")),
            include_fields=["tags", "updatedAt"]
        )
        
        logger.info(f"Found {len(results)} fact sheets in LeanIX")
        
        # Extract fact sheet IDs for detailed retrieval
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


async def fetch_leanix_details_node(state: AgentState) -> dict[str, Any]:
    """
    Fetch detailed information for LeanIX fact sheets
    """
    fact_sheet_ids = state.get('leanix_fact_sheet_ids', [])
    logger.info(f"Fetching details for {len(fact_sheet_ids)} LeanIX fact sheets")
    
    fact_sheets_detail = []
    errors = []
    
    for fs_id in fact_sheet_ids:
        try:
            # Fetch detailed fact sheet information
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


async def save_leanix_to_s3_node(state: AgentState) -> dict[str, Any]:
    """
    Save LeanIX fact sheets to S3
    """
    fact_sheets = state.get('leanix_fact_sheets_detail', [])
    logger.info(f"Saving {len(fact_sheets)} LeanIX fact sheets to S3")
    
    s3_urls = []
    errors = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for idx, fs in enumerate(fact_sheets):
        try:
            fs_id = fs.get('id', f'factsheet_{idx}')
            name = fs.get('name', fs.get('displayName', 'Untitled'))
            fs_type = fs.get('type', 'Unknown')
            
            # Build S3 key
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            s3_key = f"leanix-factsheets/{timestamp}/{fs_type}/{fs_id}_{safe_name}.json"
            
            # Upload to S3
            s3_client.put_object(
                Bucket=S3_BUCKET,
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
            
            s3_url = f"s3://{S3_BUCKET}/{s3_key}"
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


async def summarize_leanix_node(state: AgentState) -> dict[str, Any]:
    """
    Summarize LeanIX fact sheets and generate final response
    """
    logger.info("Summarizing LeanIX fact sheets and generating final response")
    
    try:
        fact_sheets = state.get('leanix_fact_sheets_detail', [])
        
        # Prepare fact sheet summary
        fs_summary = []
        for fs in fact_sheets:
            fs_summary.append({
                'name': fs.get('name', fs.get('displayName', 'Untitled')),
                'type': fs.get('type', 'Unknown'),
                'description': fs.get('description', 'No description'),
                'id': fs.get('id', ''),
                'tags': [tag.get('name', '') for tag in fs.get('tags', [])],
                'updated_at': fs.get('updatedAt', '')
            })
        
        # Generate summary using structured output
        structured_llm = llm.with_structured_output(DocumentSummary)
        
        # Build system message
        base_system_content = """You are a LeanIX Enterprise Architecture assistant. Based on the user's question and the retrieved fact sheets, provide accurate and helpful answers about the organization's applications, data, processes, and IT landscape.

Requirements:
1. Answer the user's question directly based on the fact sheets
2. Extract key insights and patterns
3. Highlight important relationships and dependencies
4. Mention relevant tags and metadata
5. Keep the answer clear and actionable"""
        
        if state.get('system_prompt'):
            system_content = f"{state['system_prompt']}\n\n{base_system_content}"
        else:
            system_content = base_system_content
        
        system_msg = SystemMessage(content=system_content)
        
        user_content = f"""
User question: {state['user_prompt']}

Retrieved LeanIX Fact Sheets (total: {len(fs_summary)}):
Search type: {state.get('leanix_search_type', 'All Types')}

"""
        for i, fs in enumerate(fs_summary, 1):
            user_content += f"""
{i}. {fs['name']} ({fs['type']})
   ID: {fs['id']}
   Description: {fs['description']}
   Tags: {', '.join(fs['tags']) if fs['tags'] else 'None'}
   Last Updated: {fs['updated_at']}

"""
        
        human_msg = HumanMessage(content=user_content)
        
        # Call LLM to generate structured summary
        result = await structured_llm.ainvoke([system_msg, human_msg])  # type: ignore
        
        # Build final response
        final_response = f"""{result['answer']}

**Key Insights:**
"""
        for i, point in enumerate(result['key_points'], 1):
            final_response += f"{i}. {point}\n"
        
        final_response += "\n**Referenced Fact Sheets:**\n"
        for ref in result['references']:
            final_response += f"- {ref['title']}\n"
        
        s3_urls = state.get('leanix_s3_urls', [])
        if s3_urls:
            final_response += "\n---\n📊 Fact sheets saved to S3:\n"
            for url in s3_urls:
                final_response += f"- {url}\n"
        
        if state.get('errors'):
            final_response += f"\n⚠️ Warning: {len(state['errors'])} error(s) occurred during processing."
        
        logger.info("LeanIX summary generated successfully")
        
        return {
            "summary": result['answer'],
            "final_response": final_response,
            "messages": [human_msg]
        }
        
    except Exception as e:
        error_msg = f"LeanIX summarization failed: {str(e)}"
        logger.error(error_msg)
        return {
            "summary": "Failed to generate summary",
            "final_response": f"Sorry, unable to generate summary. Error: {str(e)}",
            "errors": [error_msg]
        }
