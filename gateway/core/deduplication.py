import logging
from typing import Optional, List
from gateway.config import settings
from gateway.db.qdrant_client import qdrant_manager

logger = logging.getLogger(__name__)

class Deduplicator:
    """
    Semantic de-duplication heuristic checker.
    Validates whether a new memory entry represents unique context.
    """
    @staticmethod
    async def find_duplicate(vector: List[float], project_id: str, namespace: str) -> Optional[str]:
        """
        Scans Qdrant collections to locate identical semantic concepts.
        If similarity exceeds DEDUP_SIMILARITY_THRESHOLD (0.92), returns matching memory_id.
        """
        threshold = settings.DEDUP_SIMILARITY_THRESHOLD
        logger.debug(f"Executing de-duplication check for project {project_id} (threshold: {threshold})")
        
        try:
            # Query the single nearest candidate (Top-1)
            matches = await qdrant_manager.search_similar(
                vector=vector,
                project_id=project_id,
                namespace=namespace,
                top_k=1
            )
            
            if not matches:
                return None
                
            nearest = matches[0]
            similarity = nearest["score"]
            memory_id = nearest["memory_id"]
            
            logger.info(f"Nearest candidate for save: id={memory_id}, cosine_similarity={similarity:.4f}")
            
            # Check against threshold boundaries
            if similarity >= threshold:
                logger.info(f"Duplicate detected! Match score {similarity:.4f} >= threshold {threshold}. Skipping write.")
                return memory_id
                
            return None
            
        except Exception as e:
            logger.error(f"Deduplication execution failure (failing open to save): {e}")
            # In case of DB query errors, fail open to avoid throwing save errors
            return None
