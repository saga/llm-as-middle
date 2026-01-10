"""Summarize LeanIX fact sheets and generate response"""
import logging
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState
from ._shared import DocumentSummary, llm

logger = logging.getLogger(__name__)


async def summarize_leanix_node(state: AgentState) -> dict[str, Any]:
    """Summarize LeanIX fact sheets and generate final response"""
    logger.info("Summarizing LeanIX fact sheets and generating final response")
    
    try:
        fact_sheets = state.get('leanix_fact_sheets_detail', [])
        
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
        
        structured_llm = llm.with_structured_output(DocumentSummary)
        
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
        result = await structured_llm.ainvoke([system_msg, human_msg])  # type: ignore
        
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
