import uvicorn
from server import mcp

if __name__ == "__main__":
    # 使用SSE transport
    # FastMCP的run方法会自动启动服务器
    # 默认监听在127.0.0.1:8000，但我们可以通过环境变量或直接用uvicorn控制
    
    # 方式1: 使用FastMCP的run方法（简单但不能自定义host/port）
    # mcp.run(transport="sse")
    
    # 方式2: 获取ASGI应用并用uvicorn运行（可自定义配置）
    app = mcp.sse_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )