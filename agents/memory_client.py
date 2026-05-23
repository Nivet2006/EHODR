"""
UAMS Universal AI Memory Client SDK.
Import this adapter in any LLM agent or autonomous workflow script.
"""

import os
import httpx
from typing import Optional, List, Dict, Any

class UniversalMemoryClient:
    """
    Agent-agnostic memory client. Works with:
    - OpenAI Agents SDK
    - Claude (via custom tool structures)
    - Google Antigravity custom skills
    - LangChain / LlamaIndex custom tools
    - Custom python agent frameworks
    """
    def __init__(
        self,
        gateway_url: Optional[str] = None,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        agent_id: str = "unknown"
    ):
        # Read from environment variables if not passed explicitly in constructor
        self.gateway_url = gateway_url or os.environ.get("MEMORY_GATEWAY_URL", "http://localhost:8000")
        self.api_key = api_key or os.environ.get("MEMORY_API_KEY")
        self.project_id = project_id or os.environ.get("MEMORY_PROJECT_ID")
        self.agent_id = agent_id
        
        if not self.api_key:
            raise ValueError(
                "MEMORY_API_KEY is required. Pass in constructor or set MEMORY_API_KEY env var."
            )
        if not self.project_id:
            raise ValueError(
                "MEMORY_PROJECT_ID is required. Pass in constructor or set MEMORY_PROJECT_ID env var."
            )
            
        # Configure standard HTTP authentication headers
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def save(
        self,
        content: str,
        memory_type: str,
        namespace: str = "general",
        tags: Optional[List[str]] = None,
        importance_score: float = 0.5,
        source_context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Saves a semantic memory entry.
        Returns: memory_id (str) of the newly created or pre-existing duplicate record.
        """
        url = f"{self.gateway_url}/v1/memory/save"
        payload = {
            "content": content,
            "project_id": self.project_id,
            "namespace": namespace,
            "agent_id": self.agent_id,
            "memory_type": memory_type,
            "tags": tags or [],
            "importance_score": importance_score,
            "source_context": source_context,
            "metadata": metadata or {}
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, headers=self._headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["memory_id"]
            except httpx.HTTPStatusError as e:
                # Log detailed API failures
                raise RuntimeError(f"Memory save operation failed: {e.response.text}")
            except Exception as e:
                raise RuntimeError(f"Failed to communicate with memory gateway: {e}")

    async def recall(
        self,
        query: str,
        namespace: str = "general",
        top_k: int = 5
    ) -> str:
        """
        Recalls semantically matching memories for a query.
        Returns: A formatted string prompt context block ready to inject directly into a system message.
        """
        url = f"{self.gateway_url}/v1/memory/recall"
        payload = {
            "query": query,
            "project_id": self.project_id,
            "namespace": namespace,
            "top_k": top_k
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, headers=self._headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result["context_block"]
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Memory recall operation failed: {e.response.text}")
            except Exception as e:
                raise RuntimeError(f"Failed to communicate with memory gateway: {e}")
