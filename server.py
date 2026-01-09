from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

from agent import run_agent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mcp = FastMCP("confluence-intelligent-agent")

@mcp.tool()
async def ask_confluence(user_prompt: str) -> str:
    """
    智能Confluence助手 - 自动搜索、获取、保存和总结Confluence文档
    
    这个工具会：
    1. 分析您的问题，生成最佳搜索查询
    2. 搜索Confluence相关页面
    3. 获取页面完整内容
    4. 将内容保存到S3（备份）
    5. 基于页面内容总结并回答您的问题
    
    使用示例：
    - "API认证的最佳实践是什么？"
    - "最新的系统架构设计文档在哪里？"
    - "关于数据库迁移的操作步骤"
    - "团队的编码规范有哪些？"
    
    Args:
        user_prompt: 您的问题或需求（用自然语言描述）
    
    Returns:
        详细的回答，包含相关文档链接和S3备份位置
    """
    logger.info(f"Received user prompt: {user_prompt}")
    
    try:
        # 运行Agent工作流
        result = await run_agent(user_prompt)
        
        if result["success"]:
            logger.info(f"Successfully processed request. Found {result['pages_count']} pages.")
            return result["response"]
        else:
            logger.error(f"Agent execution failed: {result['errors']}")
            return f"抱歉，处理您的请求时遇到问题：\n{result['response']}"
            
    except Exception as e:
        logger.error(f"Unexpected error in ask_confluence: {e}", exc_info=True)
        return f"系统错误：{str(e)}\n请稍后重试或联系管理员。"

# 添加健康检查路由
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """健康检查端点"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "enterprise-doc-agent"}
    )
