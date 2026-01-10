"""Summarize Confluence pages and generate response"""
import logging
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState
from ._shared import DocumentSummary, llm

logger = logging.getLogger(__name__)


async def summarize_node(state: AgentState) -> dict[str, Any]:
    """Node 5: Summarize page content and generate final response"""
    logger.info("Summarizing pages and generating final response")
    
    try:
        pages_summary = []
        for page in state['pages_content']:
            metadata = page.get('metadata', {})
            content_data = metadata.get('content', {})
            
            pages_summary.append({
                'title': metadata.get('title', 'Untitled'),
                'url': metadata.get('url', ''),
                'content_preview': content_data.get('value', '')[:500]
            })
        
        structured_llm = llm.with_structured_output(DocumentSummary)
        
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
        result = await structured_llm.ainvoke([system_msg, human_msg])  # type: ignore
        
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
