from sqlalchemy.ext.asyncio import AsyncSession
from gateway.db.postgres import get_db_session
from gateway.db.qdrant_client import qdrant_manager, QdrantClientManager
from gateway.db.redis_client import redis_manager, RedisClientManager

def get_qdrant() -> QdrantClientManager:
    """
    Returns the active Qdrant manager wrapper singleton.
    """
    qdrant_manager.connect()
    return qdrant_manager

def get_redis() -> RedisClientManager:
    """
    Returns the active Redis client manager wrapper singleton.
    """
    redis_manager.connect()
    return redis_manager
