"""Microsoft Authentication Library (MSAL) authentication module"""
import os
import logging
from typing import Optional
import msal

logger = logging.getLogger(__name__)


class MSALTokenManager:
    """MSAL Token Manager"""
    
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.scope = os.getenv("AZURE_SCOPE", "https://cognitiveservices.azure.com/.default")
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError(
                "Missing required Azure authentication configuration. Please set the following environment variables:\n"
                "- AZURE_TENANT_ID\n"
                "- AZURE_CLIENT_ID\n"
                "- AZURE_CLIENT_SECRET"
            )
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
        
        self._cached_token: Optional[dict] = None
    
    def get_token(self) -> str:
        """
        Get access token
        
        Returns:
            str: Access token
        
        Raises:
            Exception: Raised when token acquisition fails
        """
        try:
            # First try to get token from cache
            result = self.app.acquire_token_silent(
                scopes=[self.scope],
                account=None
            )
            
            # If not in cache, get new token
            if not result:
                logger.info(f"Acquiring new token from {self.authority}")
                result = self.app.acquire_token_for_client(scopes=[self.scope])
            
            if result and "access_token" in result:
                self._cached_token = result
                logger.info("Successfully acquired access token")
                return result["access_token"]  # type: ignore
            else:
                error = result.get("error") if result else "Unknown error"  # type: ignore
                error_description = result.get("error_description", "") if result else ""  # type: ignore
                error_msg = f"Failed to acquire access token: {error} - {error_description}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Token acquisition error: {e}", exc_info=True)
            raise


# Global Token Manager instance
_token_manager: Optional[MSALTokenManager] = None


def get_token_manager() -> MSALTokenManager:
    """Get global Token Manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = MSALTokenManager()
    return _token_manager


def get_access_token() -> str:
    """
    Convenience function to get access token
    
    Returns:
        str: Access token
    """
    return get_token_manager().get_token()


def get_token_headers() -> dict[str, str]:
    """
    Get HTTP headers containing authentication token
    
    Returns:
        dict: Dictionary containing Authorization header
    """
    token = get_access_token()
    return {
        "Authorization": f"Bearer {token}"
    }
