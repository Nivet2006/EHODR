from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from gateway.config import settings
from typing import AsyncGenerator

# Configure the async SQL base engine using postgresql+asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True during low-level debug sessions
    pool_pre_ping=True,  # Proactively inspect connection health
    pool_size=10,        # Default size of pooled connections
    max_overflow=20      # Permitted peak overflow connections
)

# Set up the async session builder
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Declarative ORM base class
Base = declarative_base()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injection provider.
    Yields an active async database session and guarantees closure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
