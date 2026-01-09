"""LangGraph Agent节点定义"""
import os
import json
import logging
from datetime import datetime
from typing import Any
import boto3
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from clients.confluence import search_pages, get_page
from .state import AgentState

logger = logging.getLogger(__name__)

# 初始化LLM
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4"),
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base=os.getenv("OPENAI_API_BASE")
)

# 初始化S3客户端
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)
S3_BUCKET = os.getenv("S3_BUCKET", "confluence-docs-backup")


async def analyze_prompt_node(state: AgentState) -> dict[str, Any]:
    """节点1: 分析用户prompt，生成搜索查询"""
    logger.info(f"Analyzing user prompt: {state['user_prompt']}")
    
    try:
        # 使用LLM分析用户意图，生成Confluence搜索查询
        system_msg = SystemMessage(content="""
你是一个Confluence搜索助手。根据用户的问题，生成最合适的Confluence CQL搜索查询。

规则：
- 如果用户问题包含具体的主题词，使用 text ~ "关键词" 或 siteSearch ~ "关键词"
- 如果需要最新内容，添加时间过滤：lastModified > startOfMonth("-1M")
- 如果用户指定了space，添加：space = "SPACE_KEY"
- 保持查询简洁有效

只返回CQL查询字符串，不要其他内容。
        """)
        
        human_msg = HumanMessage(content=f"用户问题：{state['user_prompt']}\n\n生成Confluence搜索查询：")
        
        response = await llm.ainvoke([system_msg, human_msg])
        search_query = response.content.strip()
        
        logger.info(f"Generated search query: {search_query}")
        
        return {
            "search_query": search_query,
            "messages": [human_msg, response]
        }
    except Exception as e:
        logger.error(f"Error in analyze_prompt_node: {e}")
        return {
            "search_query": f'text ~ "{state["user_prompt"]}"',  # 回退到简单查询
            "errors": [f"Prompt analysis failed: {str(e)}"]
        }


async def search_confluence_node(state: AgentState) -> dict[str, Any]:
    """节点2: 搜索Confluence"""
    logger.info(f"Searching Confluence with query: {state['search_query']}")
    
    try:
        # 搜索Confluence
        results = await search_pages(
            query=state['search_query'],
            limit=int(os.getenv("SEARCH_LIMIT", "10"))
        )
        
        # 提取页面链接
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
    """节点3: 获取页面内容"""
    logger.info(f"Fetching {len(state['page_links'])} pages")
    
    pages_content = []
    errors = []
    
    for page_id in state['page_links']:
        try:
            # 获取页面内容
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
    """节点4: 保存内容到S3"""
    logger.info(f"Saving {len(state['pages_content'])} pages to S3")
    
    s3_urls = []
    errors = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for idx, page in enumerate(state['pages_content']):
        try:
            # 提取页面元数据
            metadata = page.get('metadata', {})
            page_id = metadata.get('id', f'page_{idx}')
            title = metadata.get('title', 'Untitled')
            
            # 构建S3 key
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            s3_key = f"confluence-docs/{timestamp}/{page_id}_{safe_title}.json"
            
            # 上传到S3
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
    """节点5: 总结页面内容并生成最终响应"""
    logger.info("Summarizing pages and generating final response")
    
    try:
        # 准备页面内容摘要
        pages_summary = []
        for page in state['pages_content']:
            metadata = page.get('metadata', {})
            content_data = metadata.get('content', {})
            
            pages_summary.append({
                'title': metadata.get('title', 'Untitled'),
                'url': metadata.get('url', ''),
                'content_preview': content_data.get('value', '')[:500]  # 前500字符
            })
        
        # 构建提示词
        system_msg = SystemMessage(content="""
你是一个Confluence文档助手。根据用户的问题和检索到的Confluence页面，提供准确、有用的回答。

要求：
1. 直接回答用户的问题
2. 引用相关页面的内容作为依据
3. 提供页面标题和URL以便用户查看原文
4. 如果页面内容不完全匹配问题，说明这一点
5. 保持回答简洁明了
        """)
        
        user_content = f"""
用户问题：{state['user_prompt']}

检索到的Confluence页面（共{len(pages_summary)}个）：

"""
        for i, page in enumerate(pages_summary, 1):
            user_content += f"""
{i}. 【{page['title']}】
   URL: {page['url']}
   内容预览: {page['content_preview']}...

"""
        
        user_content += "\n请根据以上信息回答用户的问题。"
        
        human_msg = HumanMessage(content=user_content)
        
        # 调用LLM生成总结
        response = await llm.ainvoke([system_msg, human_msg])
        summary = response.content
        
        # 构建最终响应
        final_response = f"""{summary}

---
📚 相关文档已保存到S3:
"""
        for url in state['s3_urls']:
            final_response += f"- {url}\n"
        
        if state.get('errors'):
            final_response += f"\n⚠️ 注意: 处理过程中出现了{len(state['errors'])}个错误，部分内容可能不完整。"
        
        logger.info("Summary generated successfully")
        
        return {
            "summary": summary,
            "final_response": final_response,
            "messages": [human_msg, response]
        }
        
    except Exception as e:
        error_msg = f"Summarization failed: {str(e)}"
        logger.error(error_msg)
        return {
            "summary": "总结生成失败",
            "final_response": f"抱歉，无法生成总结。错误：{str(e)}",
            "errors": [error_msg]
        }
