import logging
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from gateway.config import settings

logger = logging.getLogger(__name__)

class QdrantClientManager:
    """
    Asynchronous Qdrant client manager wrapper.
    Orchestrates vector CRUD operations, indexing filters, and similarity lookups.
    """
    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
        self.collection: str = settings.QDRANT_COLLECTION

    def connect(self):
        """
        Initializes connection resource instances.
        """
        if not self.client:
            logger.info(f"Connecting async Qdrant client to {settings.QDRANT_HOST}:{settings.QDRANT_PORT}...")
            self.client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

    async def disconnect(self):
        """
        Closes connection channels.
        """
        if self.client:
            logger.info("Closing Qdrant async connections...")
            await self.client.close()
            self.client = None

    async def upsert_vector(self, memory_id: str, vector: List[float], payload: Dict[str, Any]) -> bool:
        """
        Persists a vector embedding along with its descriptive payload.
        """
        if not self.client:
            raise RuntimeError("Qdrant client not initialized. Call connect() first.")
        try:
            point = PointStruct(
                id=memory_id,
                vector=vector,
                payload=payload
            )
            await self.client.upsert(
                collection_name=self.collection,
                points=[point]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vector {memory_id} in Qdrant: {e}")
            raise e

    async def search_similar(
        self, 
        vector: List[float], 
        project_id: str, 
        namespace: str = "general", 
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes an Approximate Nearest Neighbor search filtered by project isolation parameters.
        Returns: Matches containing similarity score, memory id, and payload.
        """
        if not self.client:
            raise RuntimeError("Qdrant client not initialized.")
        try:
            # Build filters for indexing
            query_filter = Filter(
                must=[
                    FieldCondition(key="project_id", match=MatchValue(value=project_id)),
                    FieldCondition(key="namespace", match=MatchValue(value=namespace))
                ]
            )
            
            # Execute search
            results = await self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                query_filter=query_filter,
                limit=top_k,
                score_threshold=score_threshold,
                with_payload=True
            )
            
            # Translate qdrant result models to clean python dictionaries
            formatted = []
            for item in results:
                formatted.append({
                    "memory_id": item.id,
                    "score": item.score,
                    "payload": item.payload
                })
            return formatted
        except Exception as e:
            logger.error(f"Qdrant ANN similarity search failure: {e}")
            raise e

    async def delete_vector(self, memory_id: str) -> bool:
        """
        Performs transactional point removal by ID.
        """
        if not self.client:
            raise RuntimeError("Qdrant client not initialized.")
        try:
            await self.client.delete(
                collection_name=self.collection,
                points_selector=[memory_id]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete vector {memory_id} from Qdrant: {e}")
            raise e

    async def is_healthy(self) -> bool:
        """
        Checks cluster/container connection health status.
        """
        if not self.client:
            return False
        try:
            # Qdrant client uses cluster checks or list_collections as simple ping
            await self.client.get_collections()
            return True
        except Exception:
            return False

# Export unified singleton manager
qdrant_manager = QdrantClientManager()
