#!/usr/bin/env alias python
"""
UAMS Qdrant Vector Collection Initialization Script.
Bootstraps target collections, optimizes indices, and creates search indexes.
"""

import os
import asyncio
import sys
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    HnswConfigDiff,
    OptimizersConfigDiff,
    PayloadSchemaType,
)

# Load configuration parameters with safe dev defaults
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "1536"))
COLLECTION_NAME = os.environ.get("QDRANT_COLLECTION", "ai_memories")

async def init_collection():
    """
    Validates and bootstraps the vector index collection:
    1. Connects to Qdrant via asynchronous host channels.
    2. Scans for pre-existing collection names to prevent data loss.
    3. Builds the collection with Cosine similarity distance parameters.
    4. Fine-tunes HNSW graph configurations for speed-accuracy balance.
    5. Sets payload keyword/float indexes for lightning-fast filtered ANN lookups.
    """
    print(f"Connecting to Qdrant instance at {QDRANT_HOST}:{QDRANT_PORT}...")
    
    # Initialize connection client
    client = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    
    try:
        # Check current databases
        existing = await client.get_collections()
        names = [c.name for c in existing.collections]
        
        if COLLECTION_NAME in names:
            print(f"Collection '{COLLECTION_NAME}' already exists. Skipping initialization.")
            await client.close()
            return
            
        print(f"Creating collection '{COLLECTION_NAME}' with {EMBEDDING_DIMENSIONS}-dim vectors...")
        
        # Configure HNSW and optimizer metrics
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=Distance.COSINE,
            ),
            hnsw_config=HnswConfigDiff(
                m=16,               # Max links per node. Higher = more recall accuracy, higher memory consumption.
                ef_construct=100,   # Nodes checked during build. Higher = slower build, better accuracy.
            ),
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=20000, # Starts building index when 20k points are reached.
            )
        )
        
        print("Creating operational payload indices for semantic filters...")
        
        # Create schema payloads to speed up filtered search queries
        await client.create_payload_index(COLLECTION_NAME, "project_id", PayloadSchemaType.KEYWORD)
        await client.create_payload_index(COLLECTION_NAME, "namespace", PayloadSchemaType.KEYWORD)
        await client.create_payload_index(COLLECTION_NAME, "memory_type", PayloadSchemaType.KEYWORD)
        await client.create_payload_index(COLLECTION_NAME, "importance_score", PayloadSchemaType.FLOAT)
        await client.create_payload_index(COLLECTION_NAME, "created_at", PayloadSchemaType.KEYWORD)
        
        print(f"[SUCCESS] Collection '{COLLECTION_NAME}' successfully initialized and optimized.")
        
    except Exception as e:
        print(f"[ERROR] Error during collection initialization: {e}", file=sys.stderr)
        raise e
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(init_collection())
