from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
import uuid

class MemoryEntry(BaseModel):
    """
    Universal memory schema. Compatible with all agent frameworks.
    Do not add agent-specific fields here — use metadata dict instead.
    """
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(
        ..., 
        min_length=10, 
        max_length=8000, 
        description="The distilled knowledge to persist. NOT raw conversation."
    )
    project_id: str = Field(..., description="Isolates memory by project. Required.")
    namespace: str = Field(
        default="general", 
        description="Sub-category within project: 'architecture', 'decisions', 'tasks', etc."
    )
    agent_id: str = Field(..., description="Which agent saved this: 'claude', 'gpt-4', 'gemini', 'local'")
    
    tags: List[str] = Field(
        default_factory=list, 
        max_items=20, 
        description="Semantic tags for filtering. e.g. ['database', 'qdrant', 'phase-4']"
    )
    
    memory_type: Literal[
        "architecture_decision",
        "deployment_note",
        "coding_standard",
        "api_contract",
        "workflow_state",
        "debug_resolution",
        "research_summary",
        "project_preference",
        "long_term_task",
        "general_knowledge"
    ] = Field(..., description="Categorizes the memory for retrieval filtering")
    
    importance_score: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="0.0 = low, 1.0 = critical. Used in ranking."
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: Optional[datetime] = None
    access_count: int = Field(default=0)
    
    source_context: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Brief note on WHY this was saved. Optional."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Agent-specific or project-specific extra fields"
    )

class MemorySaveRequest(BaseModel):
    """
    Request parameters for creating/saving a new memory.
    """
    content: str = Field(..., min_length=10, max_length=8000)
    project_id: str
    namespace: str = "general"
    agent_id: str
    memory_type: Literal[
        "architecture_decision",
        "deployment_note",
        "coding_standard",
        "api_contract",
        "workflow_state",
        "debug_resolution",
        "research_summary",
        "project_preference",
        "long_term_task",
        "general_knowledge"
    ]
    tags: List[str] = Field(default_factory=list)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    source_context: Optional[str] = Field(None, max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MemorySaveResponse(BaseModel):
    """
    Response model returned on successful memory persistence.
    """
    memory_id: str
    status: str = "saved"

class MemoryRecallRequest(BaseModel):
    """
    Request schema for semantic recall context lookup.
    """
    query: str = Field(..., min_length=3, max_length=2000)
    project_id: str
    namespace: str = "general"
    top_k: int = Field(default=5, ge=1, le=50)

class RecalledMemoryDetail(BaseModel):
    """
    Represents matching memories along with search relevance scores.
    """
    memory: MemoryEntry
    similarity_score: float
    composite_score: float

class MemoryRecallResponse(BaseModel):
    """
    Response block injected directly into system prompts.
    """
    context_block: str
    memories: List[RecalledMemoryDetail]

class MemorySearchRequest(BaseModel):
    """
    Request model for human-facing memory lists with metadata filters.
    """
    project_id: str
    query: Optional[str] = None
    namespace: Optional[str] = None
    memory_type: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)

class MemorySearchResponse(BaseModel):
    """
    Result lists from metadata search.
    """
    memories: List[MemoryEntry]

class MemoryDeleteResponse(BaseModel):
    """
    Status response from deleting a memory block.
    """
    memory_id: str
    status: str = "deleted"
