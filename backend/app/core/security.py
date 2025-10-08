"""
Security utilities for authentication and authorization.
"""

from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings


security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials) -> bool:
    """
    Verify the API key from the Authorization header.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        bool: True if API key is valid
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.credentials != settings.api_secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True


def get_current_api_key(credentials: HTTPAuthorizationCredentials = security) -> str:
    """
    Get and verify the current API key.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        str: The verified API key
    """
    verify_api_key(credentials)
    return credentials.credentials
