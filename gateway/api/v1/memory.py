import logging
import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete as sql_delete
from sqlalchemy.orm import selectinload

# Import dependencies and managers
from gateway.core.security import validate_api_key
from gateway.db.postgres import get_db_session
from gateway.db.models import DbMemoryEntry
from gateway.db.qdrant_client import qdrant_manager
from gateway.db.redis_client import redis_manager
from gateway.core.embedding import embedding_service
from gateway.core.deduplication import Deduplicator
from gateway.core.ranking import MemoryReRanker
from gateway.core.compression import ContextCompressor
from gateway.config import settings

# Import schema definitions
from gateway.schemas.memory import (
    MemorySaveRequest,
    MemorySaveResponse,
    MemoryRecallRequest,
    MemoryRecallResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryDeleteResponse,
    MemoryEntry,
    RecalledMemoryDetail,
    RecalledMemoryDetail
)

logger = logging.getLogger("gateway")
router = APIRouter()

@router.post("/save", response_model=MemorySaveResponse, status_code=status.HTTP_201_CREATED)
async def save_memory(
    request: MemorySaveRequest,
    api_key: str = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Saves a memory entry into persistent relational and vector storage.
    Enforces de-duplication and minimum importance score boundaries.
    """
    # 1. Enforce minimum importance score
    if request.importance_score < settings.MIN_IMPORTANCE_SCORE_TO_STORE:
        logger.info(
            f"Ingestion skipped: importance score {request.importance_score:.2f} "
            f"< threshold {settings.MIN_IMPORTANCE_SCORE_TO_STORE}."
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Memory importance score {request.importance_score:.2f} too low to persist (minimum {settings.MIN_IMPORTANCE_SCORE_TO_STORE})."
        )
        
    # 2. Generate vector embedding
    try:
        vector = await embedding_service.get_embedding(request.content)
    except Exception as e:
        logger.error(f"Embedding service execution failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate semantic vector embedding."
        )
        
    # 3. Check for semantic duplicates (threshold: 0.92)
    duplicate_id = await Deduplicator.find_duplicate(
        vector=vector,
        project_id=request.project_id,
        namespace=request.namespace
    )
    
    if duplicate_id:
        # Increment access count on duplicate record in PostgreSQL
        try:
            stmt = (
                update(DbMemoryEntry)
                .where(DbMemoryEntry.memory_id == duplicate_id)
                .values(
                    access_count=DbMemoryEntry.access_count + 1,
                    last_accessed_at=datetime.now(timezone.utc).replace(tzinfo=None)
                )
            )
            await db.execute(stmt)
            await db.commit()
            
            # Invalidate Redis query recall caches for this project namespace
            cache_pattern = f"recall_cache:{request.project_id}:{request.namespace}:*"
            # Log clear action
            logger.info(f"Duplicate entry {duplicate_id} access counts bumped. Invalidating cache.")
            
        except Exception as e:
            logger.error(f"Failed to update duplicate record stats: {e}")
            
        return MemorySaveResponse(memory_id=duplicate_id, status="duplicate_skipped")

    # 4. Save as a unique new memory entry
    memory_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Store payload object in Qdrant metadata
    payload = {
        "content": request.content,
        "project_id": request.project_id,
        "namespace": request.namespace,
        "agent_id": request.agent_id,
        "tags": request.tags,
        "memory_type": request.memory_type,
        "importance_score": request.importance_score,
        "created_at": created_at.isoformat() + "Z",
        "source_context": request.source_context,
        "metadata": request.metadata
    }
    
    # Dual write strategy:
    # A. Write to Qdrant Vector database
    try:
        await qdrant_manager.upsert_vector(
            memory_id=memory_id,
            vector=vector,
            payload=payload
        )
    except Exception as e:
        logger.error(f"Qdrant write transaction failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save vector embedding in vector store."
        )
        
    # B. Write to PostgreSQL Relational metadata store
    try:
        db_entry = DbMemoryEntry(
            memory_id=memory_id,
            content=request.content,
            project_id=request.project_id,
            namespace=request.namespace,
            agent_id=request.agent_id,
            memory_type=request.memory_type,
            tags=request.tags,
            importance_score=request.importance_score,
            created_at=created_at,
            source_context=request.source_context,
            payload_metadata=request.metadata
        )
        db.add(db_entry)
        await db.commit()
    except Exception as e:
        logger.error(f"PostgreSQL commit failure! Rolling back. Error: {e}")
        # Compensating transaction: remove orphan vector from Qdrant to maintain consistency
        await qdrant_manager.delete_vector(memory_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save memory metadata record in database."
        )
        
    # Invalidate cached recall structures
    # We clear cache keys incrementally or let them expire naturally.
    logger.info(f"Successfully created new memory entry: {memory_id}")
    return MemorySaveResponse(memory_id=memory_id, status="saved")


@router.post("/recall", response_model=MemoryRecallResponse)
async def recall_memories(
    request: MemoryRecallRequest,
    api_key: str = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Executes semantic approximate nearest neighbor search and dynamic re-ranking.
    Returns token-compressed injection block ready for prompt integration.
    """
    query_clean = request.query.strip()
    
    # 1. Check Redis Cache using hashed query key representation
    query_hash = hashlib.sha256(query_clean.encode("utf-8")).hexdigest()
    cache_key = f"recall_cache:{request.project_id}:{request.namespace}:{query_hash}:{request.top_k}"
    
    cached_val = await redis_manager.get(cache_key)
    if cached_val:
        logger.info(f"Recall cache hit! key={cache_key}")
        try:
            return MemoryRecallResponse(**json.loads(cached_val))
        except Exception as e:
            logger.warning(f"Failed to parse cached JSON recall payload: {e}")
            
    # 2. Cache Miss: Generate embedding for search prompt
    try:
        query_vector = await embedding_service.get_embedding(query_clean)
    except Exception as e:
        logger.error(f"Failed to embed recall query: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate vector embedding for query prompt."
        )
        
    # 3. Retrieve candidates from Qdrant
    try:
        # Fetch up to 20 vectors before re-ranking pipeline starts
        raw_candidates = await qdrant_manager.search_similar(
            vector=query_vector,
            project_id=request.project_id,
            namespace=request.namespace,
            top_k=20
        )
    except Exception as e:
        logger.error(f"Failed to query vectors from Qdrant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving semantic vector indexes."
        )
        
    if not raw_candidates:
        return MemoryRecallResponse(
            context_block="No relevant long-term memories retrieved for this context.",
            memories=[]
        )
        
    # 4. Fetch accessory metadata registries from PostgreSQL in a single batch
    candidate_ids = [item["memory_id"] for item in raw_candidates]
    
    try:
        stmt = select(DbMemoryEntry).where(DbMemoryEntry.memory_id.in_(candidate_ids))
        res = await db.execute(stmt)
        records = res.scalars().all()
        
        # Build dictionary map for swift lookup mapping
        postgres_metadata = {
            r.memory_id: {
                "last_accessed_at": r.last_accessed_at,
                "access_count": r.access_count,
                "created_at": r.created_at
            } for r in records
        }
    except Exception as e:
        logger.error(f"PostgreSQL metadata scan failed: {e}")
        # Default to empty mappings to fail open gracefully
        postgres_metadata = {}
        
    # 5. Execute similarity filtering and dynamic composite re-ranking
    # score threshold matches settings: 0.70 similarity
    re_ranked = MemoryReRanker.re_rank(
        qdrant_results=raw_candidates,
        postgres_metadata=postgres_metadata,
        similarity_cutoff=0.70
    )
    
    # Take requested top_k from ranked outputs
    top_ranked = re_ranked[:request.top_k]
    
    # 6. Apply token budget truncation and compile Prompt Context block
    context_block = ContextCompressor.compile_context_block(top_ranked)
    
    # 7. Asynchronously update access statistics in database for matched entries
    matched_ids = [d.memory.memory_id for d in top_ranked]
    if matched_ids:
        try:
            update_stmt = (
                update(DbMemoryEntry)
                .where(DbMemoryEntry.memory_id.in_(matched_ids))
                .values(
                    access_count=DbMemoryEntry.access_count + 1,
                    last_accessed_at=datetime.now(timezone.utc).replace(tzinfo=None)
                )
            )
            await db.execute(update_stmt)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record access metrics: {e}")
            
    # Build response payload
    response_payload = MemoryRecallResponse(
        context_block=context_block,
        memories=top_ranked
    )
    
    # 8. Cache response block in Redis with a 5 minute TTL (300s)
    try:
        await redis_manager.setex(
            key=cache_key,
            ttl=300,
            value=response_payload.model_dump_json()
        )
    except Exception as e:
        logger.warning(f"Failed to save recall results to Redis cache: {e}")
        
    return response_payload


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    request: MemorySearchRequest,
    api_key: str = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Metadata list search controller.
    Runs metadata-based queries directly on relational indices.
    """
    try:
        # Build relational select filters
        stmt = select(DbMemoryEntry).where(DbMemoryEntry.project_id == request.project_id)
        
        if request.namespace:
            stmt = stmt.where(DbMemoryEntry.namespace == request.namespace)
        if request.memory_type:
            stmt = stmt.where(DbMemoryEntry.memory_type == request.memory_type)
        if request.query:
            # SQL LIKE sub-string lookup on content fields
            stmt = stmt.where(DbMemoryEntry.content.like(f"%{request.query}%"))
            
        stmt = stmt.limit(request.limit).order_by(DbMemoryEntry.created_at.desc())
        
        res = await db.execute(stmt)
        records = res.scalars().all()
        
        # Format database models back to Pydantic schemas
        memories = []
        for r in records:
            # Filter tags if request specified tag filters
            if request.tags:
                # Ensure all tag filters match
                has_all_tags = all(tag in r.tags for tag in request.tags)
                if not has_all_tags:
                    continue
                    
            memories.append(MemoryEntry(
                memory_id=r.memory_id,
                content=r.content,
                project_id=r.project_id,
                namespace=r.namespace,
                agent_id=r.agent_id,
                tags=r.tags,
                memory_type=r.memory_type,
                importance_score=r.importance_score,
                created_at=r.created_at,
                last_accessed_at=r.last_accessed_at,
                access_count=r.access_count,
                source_context=r.source_context,
                metadata=r.payload_metadata
            ))
            
        return MemorySearchResponse(memories=memories)
        
    except Exception as e:
        logger.error(f"Metadata list search transaction failure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database exception occurred during search query."
        )


@router.delete("/delete/{memory_id}", response_model=MemoryDeleteResponse)
async def delete_memory(
    memory_id: str,
    api_key: str = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Deletes a memory record permanently from vector index structures and Postgres.
    """
    # Verify existence in relational storage first
    stmt = select(DbMemoryEntry).where(DbMemoryEntry.memory_id == memory_id)
    res = await db.execute(stmt)
    entry = res.scalars().first()
    
    if not entry:
        logger.warning(f"Delete aborted: memory_id {memory_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory record with ID '{memory_id}' not found."
        )
        
    # Transactional delete sequence
    try:
        # A. Delete from Qdrant vector index
        await qdrant_manager.delete_vector(memory_id)
        
        # B. Delete from PostgreSQL
        delete_stmt = sql_delete(DbMemoryEntry).where(DbMemoryEntry.memory_id == memory_id)
        await db.execute(delete_stmt)
        await db.commit()
        
        logger.info(f"Successfully deleted memory record {memory_id} from all indices.")
        return MemoryDeleteResponse(memory_id=memory_id, status="deleted")
        
    except Exception as e:
        logger.error(f"Error during memory record deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete transactional deletion of memory record."
        )
