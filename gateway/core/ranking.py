import logging
import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from gateway.schemas.memory import RecalledMemoryDetail, MemoryEntry

logger = logging.getLogger(__name__)

class MemoryReRanker:
    """
    Composite memory ranking and filtering engine.
    Applies the mathematical formula:
    composite = (0.5 * similarity) + (0.3 * importance) + (0.2 * recency)
    """
    @staticmethod
    def calculate_recency(last_accessed: Optional[datetime], created_at: datetime) -> float:
        """
        Calculates exponential time decay curve metric:
        recency = e^(-decay_coefficient * days_since_last_access)
        Decay coefficient defaults to 0.05 (gives ~14 day half-life).
        """
        reference_time = last_accessed if last_accessed is not None else created_at
        
        # Determine the timezone status dynamically to avoid subtracting offset-aware from offset-naive datetimes
        if reference_time.tzinfo is not None:
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            
        # Calculate time difference in fractional days
        delta = now - reference_time
        days = max(0.0, delta.total_seconds() / 86400.0)
        
        decay_coefficient = 0.05
        recency = math.exp(-decay_coefficient * days)
        return recency

    @classmethod
    def re_rank(
        cls, 
        qdrant_results: List[Dict[str, Any]], 
        postgres_metadata: Dict[str, Dict[str, Any]],
        similarity_cutoff: float = 0.70
    ) -> List[RecalledMemoryDetail]:
        """
        Synthesizes Qdrant ANN search scores with PostgreSQL timestamp registries:
        1. Drops candidates matching below the cosine similarity threshold (0.70).
        2. Calculates the exponential recency weight.
        3. Computes the composite score.
        4. Sorts output list in descending order.
        """
        logger.debug(f"Re-ranking {len(qdrant_results)} candidates with similarity cutoff {similarity_cutoff}")
        
        re_ranked: List[RecalledMemoryDetail] = []
        
        for item in qdrant_results:
            memory_id = item["memory_id"]
            similarity = item["score"]
            payload = item["payload"]
            
            # Apply cosine threshold filter
            if similarity < similarity_cutoff:
                logger.debug(f"Candidate {memory_id} similarity score {similarity:.4f} < cutoff {similarity_cutoff}. Dropped.")
                continue
                
            # Grab access counts and timestamps from PostgreSQL metadata map
            meta_record = postgres_metadata.get(memory_id, {})
            last_accessed = meta_record.get("last_accessed_at")
            access_count = meta_record.get("access_count", 0)
            
            # Construct date parsing to prevent format failures
            created_at_val = payload.get("created_at")
            if isinstance(created_at_val, str):
                try:
                    # Parse standard ISO string formats
                    created_at = datetime.fromisoformat(created_at_val.replace("Z", "+00:00"))
                except ValueError:
                    created_at = datetime.now(timezone.utc).replace(tzinfo=None)
            elif isinstance(created_at_val, datetime):
                created_at = created_at_val
            else:
                created_at = datetime.now(timezone.utc).replace(tzinfo=None)
                
            # Compute heuristic components
            importance = float(payload.get("importance_score", 0.5))
            recency = cls.calculate_recency(last_accessed, created_at)
            
            # Calculate final composite index
            composite = (0.5 * similarity) + (0.3 * importance) + (0.2 * recency)
            
            # Reconstruct the universal MemoryEntry data schema
            entry = MemoryEntry(
                memory_id=memory_id,
                content=payload.get("content", ""),
                project_id=payload.get("project_id", ""),
                namespace=payload.get("namespace", "general"),
                agent_id=payload.get("agent_id", "unknown"),
                tags=payload.get("tags", []),
                memory_type=payload.get("memory_type", "general_knowledge"),
                importance_score=importance,
                created_at=created_at,
                last_accessed_at=last_accessed,
                access_count=access_count,
                source_context=payload.get("source_context"),
                metadata=payload.get("metadata", {})
            )
            
            re_ranked.append(RecalledMemoryDetail(
                memory=entry,
                similarity_score=similarity,
                composite_score=composite
            ))
            
        # Order descending by composite score
        re_ranked.sort(key=lambda x: x.composite_score, reverse=True)
        return re_ranked
