"""认证模块"""
from .msal_auth import get_access_token, get_token_headers

__all__ = ["get_access_token", "get_token_headers"]
