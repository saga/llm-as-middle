from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

from agent import run_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mcp = FastMCP("confluence-intelligent-agent")

@mcp.tool()
async def ask_confluence(user_prompt: str) -> str:
    """
    Intelligent Confluence Assistant - Automatically search, retrieve, save, and summarize Confluence documents
    
    This tool will:
    1. Analyze your question and generate the best search query
    2. Search for relevant Confluence pages
    3. Retrieve complete page content
    4. Save content to S3 (backup)
    5. Summarize and answer your question based on page content
    
    Usage examples:
    - "What are the best practices for API authentication?"
    - "Where is the latest system architecture design document?"
    - "Database migration operation steps"
    - "What are the team's coding standards?"
    
    Args:
        user_prompt: Your question or request (described in natural language)
    
    Returns:
        Detailed answer with relevant document links and S3 backup locations
    """
    logger.info(f"Received user prompt: {user_prompt}")
    
    try:
        # Run Agent workflow
        result = await run_agent(user_prompt)
        
        if result["success"]:
            logger.info(f"Successfully processed request. Found {result['pages_count']} pages.")
            return result["response"]
        else:
            logger.error(f"Agent execution failed: {result['errors']}")
            return f"Sorry, encountered an issue while processing your request:\n{result['response']}"
            
    except Exception as e:
        logger.error(f"Unexpected error in ask_confluence: {e}", exc_info=True)
        return f"System error: {str(e)}\nPlease try again later or contact the administrator."

# Add health check route
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "enterprise-doc-agent"}
    )
