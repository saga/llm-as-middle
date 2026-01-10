from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging
import json

from agent import run_agent
from clients.leanix import search_fact_sheets, search_applications, get_fact_sheet_types

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mcp = FastMCP("confluence-intelligent-agent")

@mcp.tool()
async def ask_confluence(user_prompt: str, system_prompt: str = "") -> str:
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
        system_prompt: Optional system instructions to guide the response style and behavior
    
    Returns:
        Detailed answer with relevant document links and S3 backup locations
    """
    logger.info(f"Received user prompt: {user_prompt}")
    if system_prompt:
        logger.info(f"System prompt provided: {system_prompt[:100]}...")
    
    try:
        # Run Agent workflow
        result = await run_agent(user_prompt, system_prompt=system_prompt)
        
        if result["success"]:
            logger.info(f"Successfully processed request. Found {result['pages_count']} pages.")
            return result["response"]
        else:
            logger.error(f"Agent execution failed: {result['errors']}")
            return f"Sorry, encountered an issue while processing your request:\n{result['response']}"
            
    except Exception as e:
        logger.error(f"Unexpected error in ask_confluence: {e}", exc_info=True)
        return f"System error: {str(e)}\nPlease try again later or contact the administrator."


@mcp.tool()
async def search_leanix(
    query: str,
    fact_sheet_type: str = "",
    limit: int = 10
) -> str:
    """
    Search LeanIX for fact sheets (Applications, DataObjects, IT Components, etc.)
    
    LeanIX is an Enterprise Architecture Management (EAM) platform that helps organizations
    manage their IT landscape, applications, data, processes, and business capabilities.
    
    This tool searches for fact sheets in LeanIX using the GraphQL API and returns
    relevant results with details about the organization's architecture.
    
    Use cases:
    - "Find all CRM applications"
    - "What applications are used in the sales department?"
    - "Show me all customer data objects"
    - "List IT components for the web infrastructure"
    - "Find deprecated applications"
    
    Args:
        query: Search term to find in fact sheet names or descriptions
        fact_sheet_type: Optional type filter. Common types:
            - Application: Business applications and software systems
            - DataObject: Data entities, databases, datasets
            - ITComponent: Infrastructure components, servers, hardware
            - BusinessCapability: Business capabilities and functions
            - Process: Business processes and workflows
            - UserGroup: Teams, departments, stakeholders
            - Project: Projects and initiatives
            - Interface: APIs and integrations
            Leave empty to search all types.
        limit: Maximum number of results to return (default: 10, max: 50)
    
    Returns:
        JSON formatted response with fact sheet details including:
        - Name and description
        - Type and ID
        - Tags and metadata
        - Last update time
        - Related fact sheets (if applicable)
    
    Required environment variables:
        - LEANIX_SUBDOMAIN: Your LeanIX workspace subdomain (e.g., "mycompany")
        - LEANIX_API_TOKEN: Your LeanIX API token for authentication
    """
    logger.info(f"Searching LeanIX: query='{query}', type='{fact_sheet_type}', limit={limit}")
    
    try:
        # Validate limit
        if limit > 50:
            limit = 50
            logger.warning("Limit capped at 50")
        
        # Search fact sheets
        results = await search_fact_sheets(
            search_term=query,
            fact_sheet_type=fact_sheet_type if fact_sheet_type else None,
            limit=limit,
            include_fields=["tags", "updatedAt", "createdAt"]
        )
        
        if not results:
            return json.dumps({
                "success": False,
                "message": "No fact sheets found matching your query.",
                "query": query,
                "type_filter": fact_sheet_type or "All Types",
                "results": []
            }, indent=2)
        
        # Format results
        formatted_results = []
        for fs in results:
            formatted_results.append({
                "id": fs.get("id", ""),
                "name": fs.get("name", fs.get("displayName", "Untitled")),
                "type": fs.get("type", "Unknown"),
                "description": fs.get("description", "No description available"),
                "tags": [tag.get("name", "") for tag in fs.get("tags", [])] if fs.get("tags") else [],
                "updated_at": fs.get("updatedAt", ""),
                "created_at": fs.get("createdAt", "")
            })
        
        response = {
            "success": True,
            "message": f"Found {len(results)} fact sheet(s)",
            "query": query,
            "type_filter": fact_sheet_type or "All Types",
            "count": len(results),
            "results": formatted_results
        }
        
        logger.info(f"Successfully found {len(results)} LeanIX fact sheets")
        return json.dumps(response, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Error in search_leanix: {e}", exc_info=True)
        error_response = {
            "success": False,
            "error": str(e),
            "message": "Failed to search LeanIX. Please check your configuration and try again.",
            "query": query
        }
        return json.dumps(error_response, indent=2)


@mcp.tool()
async def get_leanix_fact_sheet_types() -> str:
    """
    Get all available fact sheet types in your LeanIX workspace
    
    This tool retrieves the list of all fact sheet types configured in your
    LeanIX workspace. Use this to discover what types of fact sheets are available
    before searching.
    
    Common fact sheet types include:
    - Application
    - BusinessCapability
    - Process
    - DataObject
    - ITComponent
    - UserGroup
    - Project
    - Provider
    - Interface
    
    Returns:
        JSON list of available fact sheet types
    
    Required environment variables:
        - LEANIX_SUBDOMAIN: Your LeanIX workspace subdomain
        - LEANIX_API_TOKEN: Your LeanIX API token
    """
    logger.info("Fetching LeanIX fact sheet types")
    
    try:
        types = await get_fact_sheet_types()
        
        if not types:
            return json.dumps({
                "success": False,
                "message": "No fact sheet types found or unable to retrieve types.",
                "types": []
            }, indent=2)
        
        response = {
            "success": True,
            "message": f"Found {len(types)} fact sheet type(s)",
            "count": len(types),
            "types": sorted(types)
        }
        
        logger.info(f"Successfully retrieved {len(types)} fact sheet types")
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error in get_leanix_fact_sheet_types: {e}", exc_info=True)
        error_response = {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve fact sheet types from LeanIX."
        }
        return json.dumps(error_response, indent=2)


# Add health check route
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "enterprise-doc-agent"}
    )
