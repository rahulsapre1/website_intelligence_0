"""
Ultra-simple test endpoint to debug issues.
"""

import logging
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test-simple")
async def test_simple(current_user: str = Depends(get_current_user)):
    """Simple test endpoint."""
    return {"status": "success", "message": "Simple endpoint working", "user": current_user}

@router.post("/test-simple")
async def test_simple_post(current_user: str = Depends(get_current_user)):
    """Simple test endpoint with POST."""
    return {"status": "success", "message": "Simple POST endpoint working", "user": current_user}
