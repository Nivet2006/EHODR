import logging
import asyncio
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from gateway.db.postgres import get_db_session
from gateway.db.redis_client import redis_manager
from gateway.db.qdrant_client import qdrant_manager

logger = logging.getLogger("gateway")
router = APIRouter()

@router.get("", status_code=status.HTTP_200_OK)
async def check_health(
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Diagnostic endpoint verifying UAMS microservice status.
    Pings relational storage, caching systems, and vector databases concurrently.
    """
    logger.debug("Executing system-wide service health pings...")
    
    # 1. Ping PostgreSQL
    postgres_healthy = False
    try:
        # Fast query ping
        result = await asyncio.wait_for(
            db.execute(text("SELECT 1")),
            timeout=2.0
        )
        if result.scalar() == 1:
            postgres_healthy = True
    except Exception as e:
        logger.error(f"Health check ping to PostgreSQL failed: {e}")
        
    # 2. Ping Redis
    redis_healthy = await redis_manager.is_healthy()
    
    # 3. Ping Qdrant
    qdrant_healthy = await qdrant_manager.is_healthy()
    
    # Assess overall system state
    all_healthy = postgres_healthy and redis_healthy and qdrant_healthy
    system_status = "healthy" if all_healthy else "degraded"
    
    if not all_healthy:
        # Return HTTP 503 Service Unavailable if critical services are offline
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return {
        "status": system_status,
        "services": {
            "postgres": "connected" if postgres_healthy else "disconnected",
            "redis": "connected" if redis_healthy else "disconnected",
            "qdrant": "connected" if qdrant_healthy else "disconnected"
        }
    }
