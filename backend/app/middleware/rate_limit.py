"""
Rate limiting middleware using slowapi.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from app.core.config import settings

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"]  # Global rate limit
)

# Rate limit decorators for specific endpoints
analyze_rate_limit = limiter.limit(settings.analyze_rate_limit)
chat_rate_limit = limiter.limit(settings.chat_rate_limit)

# Custom rate limit exceeded handler
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    response = _rate_limit_exceeded_handler(request, exc)
    response.headers["Retry-After"] = str(exc.retry_after)
    return response
