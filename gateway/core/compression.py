import logging
from typing import List
from gateway.config import settings
from gateway.schemas.memory import RecalledMemoryDetail

logger = logging.getLogger(__name__)

class ContextCompressor:
    """
    Semantic token budget management and formatting engine.
    Prunes low-rank context blocks to guarantee prompt-safety boundaries.
    """
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimates token sizing based on character volume:
        1 token ≈ 4 characters in standard English text.
        """
        return max(1, len(text) // 4)

    @classmethod
    def compile_context_block(cls, matched_memories: List[RecalledMemoryDetail]) -> str:
        """
        Combines recalled memory records into a single, standardized, injection-ready prompt block.
        Iteratively drops low-rank elements if total size exceeds MAX_CONTEXT_TOKENS budget (4000).
        """
        max_tokens = settings.MAX_CONTEXT_TOKENS
        logger.debug(f"Compiling context block for {len(matched_memories)} items under limit {max_tokens}")
        
        # Build memory blocks iteratively, descending by priority
        compiled_parts = []
        cumulative_tokens = 0
        
        # Header wrapping
        header = "=== SYSTEM SEMANTIC MEMORY CONTEXT ===\n"
        footer = "======================================"
        cumulative_tokens += cls.estimate_tokens(header + footer)
        
        for idx, detail in enumerate(matched_memories):
            mem = detail.memory
            
            # Dynamically determine the timezone status to avoid naive/aware datetime subtraction
            if mem.created_at.tzinfo is not None:
                now = datetime.now(timezone.utc)
            else:
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                
            age_days = (now - mem.created_at).days
            
            # Format single item block
            item_block = (
                f"[{idx + 1}] (Type: {mem.memory_type}, Importance: {mem.importance_score:.1f}, "
                f"Age: {age_days} days ago)\n"
                f"Context: {mem.content}\n"
                f"Tags: {', '.join(mem.tags) if mem.tags else 'None'}\n"
                f"---\n"
            )
            
            item_tokens = cls.estimate_tokens(item_block)
            
            # Check budget constraints
            if cumulative_tokens + item_tokens > max_tokens:
                logger.warning(
                    f"Token budget exceeded! Exiting compilation at item index {idx} "
                    f"(cumulative: {cumulative_tokens} tokens, limit: {max_tokens} tokens)."
                )
                break
                
            compiled_parts.append(item_block)
            cumulative_tokens += item_tokens
            
        if not compiled_parts:
            return "No relevant long-term memories retrieved for this context."
            
        # Join components
        return header + "".join(compiled_parts) + footer
# Import datetime inside scope to prevent bootstrap namespace clashes
from datetime import datetime, timezone
