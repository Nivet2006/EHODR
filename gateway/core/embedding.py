import logging
import asyncio
import httpx
import hashlib
import numpy as np
from typing import List
from gateway.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Asynchronous Vector Embedding Generation Service.
    Supports standard OpenAI REST channels and deterministic mock pipelines for offline dev.
    """
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower()
        self.model = settings.EMBEDDING_MODEL
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self.api_key = settings.OPENAI_API_KEY
        
        # Instantiate a persistent http client for pooling
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """
        Closes external HTTP pool resources.
        """
        await self.http_client.close()

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generates a vector representation for a given piece of text.
        Executes automatic retry logic on remote transient failures.
        """
        # Strip string white-spaces
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Input text for embedding cannot be empty.")
            
        # Detect if we should use local deterministic mock pipeline (offline dev check)
        is_placeholder_key = "placeholder" in self.api_key or not self.api_key
        if self.provider == "mock" or (self.provider == "openai" and is_placeholder_key):
            logger.info("Executing local deterministic offline embedding generator...")
            return self._generate_deterministic_mock(clean_text)
            
        if self.provider == "openai":
            return await self._get_openai_embedding(clean_text)
            
        if self.provider == "ollama":
            return await self._get_ollama_embedding(clean_text)
            
        # Fallback to local mock if provider configuration is unverified
        logger.warning(f"Unrecognized provider '{self.provider}'. Falling back to local mock.")
        return self._generate_deterministic_mock(clean_text)

    async def _get_openai_embedding(self, text: str) -> List[float]:
        """
        Calls OpenAI REST API with exponential backoff retries.
        """
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": text,
            "model": self.model
        }
        
        max_retries = 3
        backoff_sec = 1.0
        
        for attempt in range(max_retries):
            try:
                response = await self.http_client.post(url, headers=headers, json=payload)
                
                # Check for rate-limiting
                if response.status_code == 429:
                    logger.warning(f"OpenAI rate limited (attempt {attempt+1}/{max_retries}). Retrying...")
                    await asyncio.sleep(backoff_sec)
                    backoff_sec *= 2
                    continue
                    
                response.raise_for_status()
                data = response.json()
                vector = data["data"][0]["embedding"]
                
                # Verify that dimensions match configured size
                if len(vector) != self.dimensions:
                    logger.error(f"Dimension mismatch! Expected {self.dimensions}, got {len(vector)}.")
                    # Return truncated or padded vector as robust recovery
                    if len(vector) > self.dimensions:
                        return vector[:self.dimensions]
                    else:
                        return vector + [0.0] * (self.dimensions - len(vector))
                        
                return vector
                
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenAI API status error: {e.response.text}")
                if attempt == max_retries - 1:
                    raise e
            except Exception as e:
                logger.error(f"Failed to fetch embedding: {e}")
                if attempt == max_retries - 1:
                    raise e
            
            # Backoff before retrying
            await asyncio.sleep(backoff_sec)
            backoff_sec *= 2
            
        raise RuntimeError("Embedding generation failed after exhausting all retry attempts.")

    async def _get_ollama_embedding(self, text: str) -> List[float]:
        """
        Calls local Ollama API to generate embeddings.
        """
        url = f"{settings.OLLAMA_URL.rstrip('/')}/api/embeddings"
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        max_retries = 3
        backoff_sec = 1.0
        
        for attempt in range(max_retries):
            try:
                response = await self.http_client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                vector = data["embedding"]
                
                # Verify that dimensions match configured size
                if len(vector) != self.dimensions:
                    logger.error(f"Dimension mismatch for Ollama! Expected {self.dimensions}, got {len(vector)}.")
                    if len(vector) > self.dimensions:
                        return vector[:self.dimensions]
                    else:
                        return vector + [0.0] * (self.dimensions - len(vector))
                        
                return vector
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama API status error: {e.response.text}")
                if attempt == max_retries - 1:
                    raise e
            except Exception as e:
                logger.error(f"Failed to fetch Ollama embedding: {e}")
                if attempt == max_retries - 1:
                    raise e
            
            await asyncio.sleep(backoff_sec)
            backoff_sec *= 2
            
        raise RuntimeError("Ollama embedding generation failed after exhausting all retry attempts.")

    def _generate_deterministic_mock(self, text: str) -> List[float]:
        """
        Generates a unit-normalized floating-point array derived from SHA-256 content hashing.
        Guarantees that identical string inputs yield identical mock embeddings, mimicking real vector DB behavior.
        """
        # Generate sha256 bytes
        sha = hashlib.sha256(text.encode("utf-8")).digest()
        
        # Build a deterministic random generator seed from the digest bytes
        seed = int.from_bytes(sha[:4], byteorder="big")
        rng = np.random.default_rng(seed)
        
        # Generate random array matching target size
        raw = rng.standard_normal(self.dimensions)
        
        # Normalize to unit length (vector magnitude = 1.0) for standard Cosine similarity evaluation
        norm = np.linalg.norm(raw)
        normalized = (raw / norm).tolist() if norm > 0 else ([0.0] * self.dimensions)
        
        return [float(x) for x in normalized]

# Export singleton instance
embedding_service = EmbeddingService()
