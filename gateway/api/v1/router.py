from fastapi import APIRouter
from gateway.api.v1.health import router as health_router
from gateway.api.v1.memory import router as memory_router
from gateway.api.v1.chat import router as chat_router

# Aggregated API router
router = APIRouter()

# Register prefix routes
router.include_router(health_router, prefix="/health", tags=["Diagnostic Health"])
router.include_router(memory_router, prefix="/memory", tags=["Semantic Memory Operations"])
router.include_router(chat_router, prefix="/chat", tags=["Augmented Conversation"])
