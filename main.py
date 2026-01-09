import uvicorn
from server import mcp

if __name__ == "__main__":
    # Use SSE transport
    # FastMCP's run method automatically starts the server
    # By default listens on 127.0.0.1:8000, but we can control via environment variables or directly with uvicorn
    
    # Method 1: Use FastMCP's run method (simple but can't customize host/port)
    # mcp.run(transport="sse")
    
    # Method 2: Get ASGI app and run with uvicorn (allows custom configuration)
    app = mcp.sse_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )