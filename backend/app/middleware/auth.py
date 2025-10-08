"""
Authentication middleware for API endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_api_key

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to get the current authenticated user (API key).
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        str: The verified API key
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        verify_api_key(credentials)
        return credentials.credentials
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
