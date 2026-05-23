from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ChatMessage(BaseModel):
    """
    Standard chat message formatting structure.
    """
    role: str = Field(..., description="Role of the sender (e.g. system, user, assistant)")
    content: str = Field(..., description="Content of the message text")

class ChatRequest(BaseModel):
    """
    Request model for memory-augmented conversation queries.
    """
    messages: List[ChatMessage] = Field(..., min_items=1, description="Historical list of thread messages")
    project_id: str = Field(..., description="Isolate memory search to this project ID")
    namespace: str = Field(default="general", description="Isolate memory search to this namespace")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class ChatResponse(BaseModel):
    """
    Standard LLM output returned from augmented prompt operations.
    """
    response: str
