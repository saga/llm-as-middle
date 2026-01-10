"""Unified client wrapper with logging and extensibility"""
import os
import logging
from typing import Any, Optional, Callable
from pydantic import SecretStr
from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI
from auth import get_access_token

logger = logging.getLogger(__name__)


# Hook管理器
class HookManager:
    """统一的钩子管理"""
    def __init__(self):
        self.before_hooks = []
        self.after_hooks = []
    
    def add_before(self, hook: Callable):
        self.before_hooks.append(hook)
    
    def add_after(self, hook: Callable):
        self.after_hooks.append(hook)
    
    def run_before(self, *args, **kwargs):
        for hook in self.before_hooks:
            try:
                hook(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Before hook failed: {e}")
    
    def run_after(self, *args, **kwargs):
        for hook in self.after_hooks:
            try:
                hook(*args, **kwargs)
            except Exception as e:
                logger.warning(f"After hook failed: {e}")


# 全局钩子管理器
_hook_manager = HookManager()


def add_before_request_hook(hook: Callable):
    """添加请求前钩子（全局）"""
    _hook_manager.add_before(hook)


def add_after_request_hook(hook: Callable):
    """添加请求后钩子（全局）"""
    _hook_manager.add_after(hook)


# LangChain ChatOpenAI包装
class ChatOpenAIWrapper(ChatOpenAI):
    """ChatOpenAI wrapper with logging"""
    
    async def ainvoke(self, messages, **kwargs):
        # Before hooks
        _hook_manager.run_before(messages, kwargs)
        
        msg_count = len(messages) if isinstance(messages, list) else 1
        logger.debug(f"LLM request: {msg_count} messages, model={self.model_name}")
        
        try:
            result = await super().ainvoke(messages, **kwargs)
            logger.debug(f"LLM response received")
            
            # After hooks
            _hook_manager.run_after(messages, kwargs, result)
            
            return result
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise
    
    def invoke(self, messages, **kwargs):
        # Before hooks
        _hook_manager.run_before(messages, kwargs)
        
        msg_count = len(messages) if isinstance(messages, list) else 1
        logger.debug(f"LLM request (sync): {msg_count} messages, model={self.model_name}")
        
        try:
            result = super().invoke(messages, **kwargs)
            logger.debug(f"LLM response received (sync)")
            
            # After hooks
            _hook_manager.run_after(messages, kwargs, result)
            
            return result
        except Exception as e:
            logger.error(f"LLM request failed (sync): {e}")
            raise


def create_chat_openai(model: Optional[str] = None, temperature: float = 0.7,
                       base_url: Optional[str] = None, api_key: Optional[str] = None,
                       **kwargs) -> ChatOpenAIWrapper:
    """创建ChatOpenAI实例（自动MSAL认证）"""
    if api_key is None:
        access_token = get_access_token()
        api_key = access_token
    else:
        access_token = api_key
    
    return ChatOpenAIWrapper(
        model=model or os.getenv("LLM_MODEL", "gpt-4"),
        temperature=temperature,
        api_key=SecretStr(api_key),
        base_url=base_url or os.getenv("LITELLM_BASE_URL", "http://localhost:4000"),
        default_headers={"Authorization": f"Bearer {access_token}"},
        **kwargs
    )


# 默认日志钩子
def log_request(request_data, *args):
    """记录请求"""
    if isinstance(request_data, dict):
        # OpenAI request
        messages = request_data.get('messages', [])
        if messages and isinstance(messages, list):
            user_msg = next((m.get('content', '') for m in messages if m.get('role') == 'user'), '')
            if user_msg:
                logger.info(f"Request: {user_msg[:100]}...")
    elif isinstance(request_data, list):
        # LangChain request
        if len(request_data) > 0:
            last_msg = request_data[-1]
            if hasattr(last_msg, 'content'):
                logger.info(f"LLM request: {str(last_msg.content)[:100]}...")


# 自动启用日志
add_before_request_hook(log_request)
