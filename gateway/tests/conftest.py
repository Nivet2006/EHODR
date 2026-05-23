import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from gateway.db.postgres import Base
from gateway.main import app

# Create isolated async engine for fast in-memory SQLite database testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates a single event loop instance for the entire test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """
    Instantiates an in-memory SQLite test database.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an isolated, transaction-rolled-back database session for each unit test.
    This guarantees zero state leakage across test cases.
    """
    AsyncSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback() # Rollback all writes after test completes

@pytest.fixture
def client(db_session) -> TestClient:
    """
    Exposes a standard FastAPI HTTP test client with database dependency overrides.
    This guarantees all endpoints write to the isolated test database.
    """
    from gateway.db.postgres import get_db_session
    
    async def override_get_db_session():
        yield db_session
        
    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
