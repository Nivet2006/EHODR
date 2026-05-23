import hashlib
import logging
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from gateway.db.redis_client import redis_manager

logger = logging.getLogger("gateway")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-Backed API Rate Limiting Middleware.
    Enforces a strict threshold of 100 requests per 60 seconds per API Key.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Bypass rate limiter checks for diagnostic health routes
        if request.url.path == "/v1/health" or request.url.path == "/health":
            return await call_next(request)
            
        # Extract Bearer token or client IP to build rate limit cache key
        auth_header = request.headers.get("Authorization", "")
        
        if auth_header.startswith("Bearer "):
            token = auth_header.split("Bearer ")[-1].strip()
            # Hash token for privacy in Redis keys
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            rate_key = f"rate_limit:{token_hash}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            rate_key = f"rate_limit_ip:{client_ip}"
            
        # Set limit variables
        max_requests = 100
        window_seconds = 60
        
        # Check limit threshold using Redis manager
        is_allowed = await redis_manager.check_rate_limit(
            key=rate_key,
            max_requests=max_requests,
            window_seconds=window_seconds
        )
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for key index {rate_key}!")
            # Build structured HTTP 429 response
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded! Maximum 100 requests per 60 seconds."
            )
            
        return await call_next(request)
