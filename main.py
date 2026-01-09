import uvicorn
from server import mcp
from starlette.applications import Starlette
from starlette.routing import Mount

if __name__ == "__main__":
    # Use HTTP transport for MCP protocol
    # Mounted at /mcp path for client access
    # Client config: {"type": "http", "url": "http://MYSERVER:8000/mcp"}
    
    app = Starlette(routes=[
        Mount("/mcp", app=mcp.get_asgi_app())
    ])
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )