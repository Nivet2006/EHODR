import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

# Import configurations and database base drivers
from gateway.config import settings
from gateway.db.postgres import engine, Base
from gateway.db.qdrant_client import qdrant_manager
from gateway.db.redis_client import redis_manager
from gateway.core.embedding import embedding_service

# Import middlewares
from gateway.middleware.logging import StructuredLoggingMiddleware
from gateway.middleware.rate_limit import RateLimitMiddleware
from gateway.middleware.error_handler import register_error_handlers

# Import routers
from gateway.api.v1.router import router as v1_router

logger = logging.getLogger("gateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages resource lifespan events for UAMS.
    Instantiates database tables, opens clients, and guarantees graceful cleanup.
    """
    logger.info("Initializing UAMS FastAPI Gateway Service...")
    
    # 1. Automate database tables bootstrapping on startup
    try:
        logger.info("Synchronizing PostgreSQL tables schemas...")
        async with engine.begin() as conn:
            # Create memories table if it does not exist
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgreSQL database tables successfully synchronized.")
    except Exception as e:
        logger.critical(f"PostgreSQL database tables synchronization failure: {e}")
        
    # 2. Connect Redis and Qdrant clients
    try:
        redis_manager.connect()
        qdrant_manager.connect()
        logger.info("Redis cache and Qdrant vector client connections initialized.")
    except Exception as e:
        logger.error(f"Downstream service client connection initialization failure: {e}")
        
    yield  # Application handles inbound requests here
    
    # 3. Graceful cleanup and connection closures on container teardown
    logger.info("Initiating UAMS FastAPI Gateway shutdown sequence...")
    try:
        await qdrant_manager.disconnect()
        await redis_manager.disconnect()
        await engine.dispose()
        await embedding_service.close()
        logger.info("UAMS container database and network connections successfully cleaned.")
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


# Create the core FastAPI application instance
app = FastAPI(
    title="Universal AI Memory System Gateway",
    description="Production-grade asynchronous persistent memory gateway for AI agent systems.",
    version="2.0.0",
    lifespan=lifespan
)

# 1. Register global exception handlers first (outermost shell)
register_error_handlers(app)

# 2. Add structured logging middleware
app.add_middleware(StructuredLoggingMiddleware)

# 3. Add rate limiting middleware (100 req / 60 sec)
app.add_middleware(RateLimitMiddleware)

# 4. Add security Trusted Host middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "gateway", "host.docker.internal", "testserver"]
)

# 5. Add cross-origin resource sharing middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow broad integrations across other agent frameworks
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. Instrument Prometheus metrics endpoint observability (/metrics)
Instrumentator().instrument(app).expose(app, include_in_schema=False)

# 7. Register operational versioned API routers
app.include_router(v1_router, prefix="/v1")


@app.get("/", include_in_schema=False)
async def root_redirect():
    """
    Redirects root requests to FastAPI's interactive Swagger documentation page.
    """
    return RedirectResponse(url="/docs")
