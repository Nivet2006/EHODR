from sqlalchemy import Column, String, Float, DateTime, Integer, JSON
from datetime import datetime
from gateway.db.postgres import Base

class DbMemoryEntry(Base):
    """
    SQLAlchemy database representation for memory metadata entries.
    Excludes the floating-point vector arrays (which live solely in Qdrant).
    """
    __tablename__ = "memories"

    # Primary Key identifier
    memory_id = Column(String(36), primary_key=True, index=True)
    
    # Core Data
    content = Column(String(8000), nullable=False)
    
    # Project & Agent Isolation keys (indexed for rapid filter parsing)
    project_id = Column(String(100), nullable=False, index=True)
    namespace = Column(String(100), nullable=False, default="general", index=True)
    agent_id = Column(String(100), nullable=False)
    
    # Semantic categories and tags
    memory_type = Column(String(50), nullable=False, index=True)
    tags = Column(JSON, nullable=False, default=list) # Stored as JSON list of tags
    
    # Heuristic ratings
    importance_score = Column(Float, nullable=False, default=0.5)
    
    # Timestamps & Activity metrics
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, nullable=False, default=0)
    
    # Extensible fields and notes
    source_context = Column(String(500), nullable=True)
    payload_metadata = Column("metadata", JSON, nullable=False, default=dict) # Catch-all dictionary for agent metadata
