import secrets
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from gateway.config import settings

logger = logging.getLogger(__name__)
security_scheme = HTTPBearer()

async def validate_api_key(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    """
    Validates the inbound Bearer Token against settings.API_SECRET_KEY.
    Uses secrets.compare_digest to prevent micro-timing attacks.
    """
    token = credentials.credentials
    expected = settings.API_SECRET_KEY
    
    # Secure, constant-time validation comparison
    is_valid = secrets.compare_digest(token, expected)
    
    if not is_valid:
        logger.warning("Authentication failure! Attempt with invalid or missing API key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API Secret Key credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return token
