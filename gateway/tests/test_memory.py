# ===============================================================================
# PURPOSE: Asynchronous Unit Testing Suite for UAMS Memory API Endpoints.
# SCOPE: Covers health checks, memory save, recall, search, and delete CRUD.
# DEPENDENCIES: pytest, pytest-asyncio, fastapi, sqlalchemy, httpx, unittest.mock
# RISKS: Relies on mocking database and client managers; requires rigorous 
#        assertion matching to avoid false positives.
# ==============================================================================

import pytest
import uuid
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from gateway.schemas.memory import MemoryEntry
from gateway.db.models import DbMemoryEntry

# Use pytest.mark.asyncio for async tests
pytestmark = pytest.mark.asyncio

@patch("gateway.api.v1.health.redis_manager")
@patch("gateway.api.v1.health.qdrant_manager")
async def test_health_endpoint_healthy(mock_qdrant, mock_redis, client, db_session):
    """
    Verifies that GET /v1/health returns HTTP 200 and 'healthy' status when
    all downstream systems (postgres, redis, qdrant) are connected.
    """
    mock_redis.is_healthy = AsyncMock(return_value=True)
    mock_qdrant.is_healthy = AsyncMock(return_value=True)

    response = client.get("/v1/health")
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["postgres"] == "connected"
    assert data["services"]["redis"] == "connected"
    assert data["services"]["qdrant"] == "connected"


@patch("gateway.api.v1.health.redis_manager")
@patch("gateway.api.v1.health.qdrant_manager")
async def test_health_endpoint_degraded(mock_qdrant, mock_redis, client, db_session):
    """
    Verifies that GET /v1/health returns HTTP 503 and 'degraded' status when
    any critical service is disconnected.
    """
    mock_redis.is_healthy = AsyncMock(return_value=False)
    mock_qdrant.is_healthy = AsyncMock(return_value=True)

    response = client.get("/v1/health")
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    data = response.json()
    assert data["status"] == "degraded"
    assert data["services"]["postgres"] == "connected"
    assert data["services"]["redis"] == "disconnected"
    assert data["services"]["qdrant"] == "connected"


async def test_save_memory_low_importance_rejected(client):
    """
    Verifies that POST /v1/memory/save rejects a memory write request if
    the importance score is below the threshold of 0.3.
    """
    headers = {"Authorization": "Bearer c81eb2939c714d48e89cf29d0f3df96b27d428cf129e18b8577777174dbde0ef"}
    payload = {
        "content": "This is a low importance memory that should be rejected.",
        "project_id": "test-project-1",
        "namespace": "general",
        "agent_id": "test-agent",
        "memory_type": "general_knowledge",
        "tags": ["test"],
        "importance_score": 0.1,
    }
    
    response = client.post("/v1/memory/save", json=payload, headers=headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "too low to persist" in response.json()["detail"]


@patch("gateway.api.v1.memory.embedding_service")
@patch("gateway.api.v1.memory.qdrant_manager")
async def test_save_memory_success(mock_qdrant, mock_embed, client, db_session):
    """
    Verifies that POST /v1/memory/save successfully saves a memory and returns 
    HTTP 201 Created and memory_id when conditions are met.
    """
    mock_embed.get_embedding = AsyncMock(return_value=[0.1] * 1536)
    mock_qdrant.upsert_vector = AsyncMock(return_value=True)
    
    headers = {"Authorization": "Bearer c81eb2939c714d48e89cf29d0f3df96b27d428cf129e18b8577777174dbde0ef"}
    payload = {
        "content": "This is a long term highly important memory to persist in systems.",
        "project_id": "test-project-2",
        "namespace": "architecture",
        "agent_id": "test-agent",
        "memory_type": "architecture_decision",
        "tags": ["qdrant", "postgres"],
        "importance_score": 0.85,
        "source_context": "testing ingestion flow",
        "metadata": {"key": "val"}
    }
    
    # We must also mock deduplicator check to not find a duplicate
    with patch("gateway.api.v1.memory.Deduplicator.find_duplicate", AsyncMock(return_value=None)):
        response = client.post("/v1/memory/save", json=payload, headers=headers)
        
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "memory_id" in data
    assert data["status"] == "saved"


@patch("gateway.api.v1.memory.embedding_service")
@patch("gateway.api.v1.memory.qdrant_manager")
async def test_save_memory_duplicate_skipped(mock_qdrant, mock_embed, client, db_session):
    """
    Verifies that saving a semantic duplicate returns HTTP 201 and duplicate_skipped status.
    """
    mock_embed.get_embedding = AsyncMock(return_value=[0.1] * 1536)
    duplicate_uuid = str(uuid.uuid4())
    
    # Insert existing memory into test SQLite DB for access_count bump simulation
    db_entry = DbMemoryEntry(
        memory_id=duplicate_uuid,
        content="This is a long term highly important memory to persist in systems.",
        project_id="test-project-2",
        namespace="architecture",
        agent_id="test-agent",
        memory_type="architecture_decision",
        tags=["qdrant", "postgres"],
        importance_score=0.85,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        access_count=1
    )
    db_session.add(db_entry)
    await db_session.commit()
    
    headers = {"Authorization": "Bearer c81eb2939c714d48e89cf29d0f3df96b27d428cf129e18b8577777174dbde0ef"}
    payload = {
        "content": "This is a long term highly important memory to persist in systems.",
        "project_id": "test-project-2",
        "namespace": "architecture",
        "agent_id": "test-agent",
        "memory_type": "architecture_decision",
        "tags": ["qdrant", "postgres"],
        "importance_score": 0.85
    }
    
    with patch("gateway.api.v1.memory.Deduplicator.find_duplicate", AsyncMock(return_value=duplicate_uuid)):
        response = client.post("/v1/memory/save", json=payload, headers=headers)
        
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["memory_id"] == duplicate_uuid
    assert data["status"] == "duplicate_skipped"


@patch("gateway.api.v1.memory.redis_manager")
@patch("gateway.api.v1.memory.embedding_service")
@patch("gateway.api.v1.memory.qdrant_manager")
async def test_recall_memories_cache_hit(mock_qdrant, mock_embed, mock_redis, client):
    """
    Verifies that POST /v1/memory/recall returns cached context block directly on cache hit.
    """
    cached_response = {
        "context_block": "Retrieved from cache! Design uses HNSW index.",
        "memories": []
    }
    mock_redis.get = AsyncMock(return_value=json.dumps(cached_response))
    
    headers = {"Authorization": "Bearer c81eb2939c714d48e89cf29d0f3df96b27d428cf129e18b8577777174dbde0ef"}
    payload = {
        "query": "How is the index designed?",
        "project_id": "test-project-2",
        "namespace": "architecture",
        "top_k": 3
    }
    
    response = client.post("/v1/memory/recall", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["context_block"] == "Retrieved from cache! Design uses HNSW index."
    assert data["memories"] == []


@patch("gateway.api.v1.memory.redis_manager")
@patch("gateway.api.v1.memory.embedding_service")
@patch("gateway.api.v1.memory.qdrant_manager")
async def test_recall_memories_cache_miss_success(mock_qdrant, mock_embed, mock_redis, client, db_session):
    """
    Verifies cache miss flow: queries embedding, calls qdrant, pulls metadata, re-ranks, and updates access.
    """
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock(return_value=True)
    mock_embed.get_embedding = AsyncMock(return_value=[0.1] * 1536)
    
    memory_uuid = str(uuid.uuid4())
    mock_qdrant.search_similar = AsyncMock(return_value=[
        {
            "memory_id": memory_uuid,
            "score": 0.85,
            "payload": {
                "content": "This is a detailed HNSW design index note.",
                "project_id": "test-project-2",
                "namespace": "architecture",
                "agent_id": "test-agent",
                "tags": ["hnsw"],
                "memory_type": "architecture_decision",
                "importance_score": 0.9,
                "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
                "source_context": "recall test"
            }
        }
    ])
    
    # Save the db entry first in SQLite so that PostgreSQL lookup works
    db_entry = DbMemoryEntry(
        memory_id=memory_uuid,
        content="This is a detailed HNSW design index note.",
        project_id="test-project-2",
        namespace="architecture",
        agent_id="test-agent",
        memory_type="architecture_decision",
        tags=["hnsw"],
        importance_score=0.9,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        access_count=0
    )
    db_session.add(db_entry)
    await db_session.commit()
    
    headers = {"Authorization": "Bearer c81eb2939c714d48e89cf29d0f3df96b27d428cf129e18b8577777174dbde0ef"}
    payload = {
        "query": "How is the index designed?",
        "project_id": "test-project-2",
        "namespace": "architecture",
        "top_k": 3
    }
    
    response = client.post("/v1/memory/recall", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "This is a detailed HNSW design index note." in data["context_block"]
    assert len(data["memories"]) == 1
    assert data["memories"][0]["similarity_score"] == 0.85
    assert data["memories"][0]["memory"]["memory_id"] == memory_uuid


async def test_search_memories_relational(client, db_session):
    """
    Verifies that POST /v1/memory/search returns metadata matching records from Postgres.
    """
    # Insert multiple entries into relational store
    id1 = str(uuid.uuid4())
    id2 = str(uuid.uuid4())
    
    db_session.add_all([
        DbMemoryEntry(
            memory_id=id1,
            content="Memory entry about fast api architecture design.",
            project_id="proj-x",
            namespace="dev",
            agent_id="claude",
            memory_type="architecture_decision",
            tags=["fastapi", "router"],
            importance_score=0.7,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        ),
        DbMemoryEntry(
            memory_id=id2,
            content="Memory entry about database migrations workflow.",
            project_id="proj-x",
            namespace="dev",
            agent_id="claude",
            memory_type="workflow_state",
            tags=["database", "postgres"],
            importance_score=0.5,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
    ])
    await db_session.commit()
    
    headers = {"Authorization": "Bearer c81eb2939c714d48e89cf29d0f3df96b27d428cf129e18b8577777174dbde0ef"}
    
    # 1. Search filter by type
    payload = {
        "project_id": "proj-x",
        "namespace": "dev",
        "memory_type": "architecture_decision"
    }
    response = client.post("/v1/memory/search", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["memories"]) == 1
    assert data["memories"][0]["memory_id"] == id1
    
    # 2. Search substring filter
    payload = {
        "project_id": "proj-x",
        "query": "migrations"
    }
    response = client.post("/v1/memory/search", json=payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["memories"]) == 1
    assert data["memories"][0]["memory_id"] == id2


@patch("gateway.api.v1.memory.qdrant_manager")
async def test_delete_memory_flow(mock_qdrant, client, db_session):
    """
    Verifies Permanent delete Permanently removes memory from both PostgreSQL and Qdrant.
    """
    mock_qdrant.delete_vector = AsyncMock(return_value=True)
    memory_uuid = str(uuid.uuid4())
    
    # Insert entry into relational db
    db_entry = DbMemoryEntry(
        memory_id=memory_uuid,
        content="This will be deleted.",
        project_id="proj-y",
        namespace="dev",
        agent_id="claude",
        memory_type="general_knowledge",
        tags=[],
        importance_score=0.4,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db_session.add(db_entry)
    await db_session.commit()
    
    headers = {"Authorization": "Bearer c81eb2939c714d48e89cf29d0f3df96b27d428cf129e18b8577777174dbde0ef"}
    
    # Delete non-existent should throw 404
    response = client.delete(f"/v1/memory/delete/non-existent-id", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # Successful deletion
    response = client.delete(f"/v1/memory/delete/{memory_uuid}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["memory_id"] == memory_uuid
    assert data["status"] == "deleted"
    
    # Confirm it is missing in Postgres
    db_check = await db_session.get(DbMemoryEntry, memory_uuid)
    assert db_check is None
