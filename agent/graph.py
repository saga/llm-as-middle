"""LangGraph工作流定义"""
import logging
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    analyze_prompt_node,
    search_confluence_node,
    fetch_pages_node,
    save_to_s3_node,
    summarize_node
)

logger = logging.getLogger(__name__)


def create_agent_graph():
    """创建Agent工作流图"""
    
    # 创建图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("analyze_prompt", analyze_prompt_node)
    workflow.add_node("search_confluence", search_confluence_node)
    workflow.add_node("fetch_pages", fetch_pages_node)
    workflow.add_node("save_to_s3", save_to_s3_node)
    workflow.add_node("summarize", summarize_node)
    
    # 定义边（工作流）
    workflow.set_entry_point("analyze_prompt")
    
    workflow.add_edge("analyze_prompt", "search_confluence")
    workflow.add_edge("search_confluence", "fetch_pages")
    workflow.add_edge("fetch_pages", "save_to_s3")
    workflow.add_edge("save_to_s3", "summarize")
    workflow.add_edge("summarize", END)
    
    # 编译图
    app = workflow.compile()
    
    logger.info("Agent graph created successfully")
    return app


# 全局实例
agent_graph = create_agent_graph()


async def run_agent(user_prompt: str) -> dict:
    """
    运行Agent处理用户请求
    
    Args:
        user_prompt: 用户的问题或请求
        
    Returns:
        包含最终响应的字典
    """
    logger.info(f"Running agent for prompt: {user_prompt}")
    
    # 初始化状态
    initial_state: AgentState = {
        "user_prompt": user_prompt,
        "search_query": "",
        "search_results": [],
        "page_links": [],
        "pages_content": [],
        "s3_urls": [],
        "summary": "",
        "final_response": "",
        "messages": [],
        "errors": []
    }
    
    try:
        # 运行图
        final_state = await agent_graph.ainvoke(initial_state)
        
        logger.info("Agent execution completed successfully")
        
        return {
            "success": True,
            "response": final_state["final_response"],
            "pages_count": len(final_state["pages_content"]),
            "s3_urls": final_state["s3_urls"],
            "errors": final_state["errors"]
        }
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        return {
            "success": False,
            "response": f"处理失败：{str(e)}",
            "pages_count": 0,
            "s3_urls": [],
            "errors": [str(e)]
        }
