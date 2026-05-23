import logging
import httpx
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from gateway.core.security import validate_api_key
from gateway.db.postgres import get_db_session
from gateway.schemas.chat import ChatRequest, ChatResponse, ChatMessage
from gateway.api.v1.memory import recall_memories
from gateway.schemas.memory import MemoryRecallRequest
from gateway.config import settings

logger = logging.getLogger("gateway")
router = APIRouter()

@router.post("", response_model=ChatResponse)
async def chat_augmented(
    request: ChatRequest,
    api_key: str = Depends(validate_api_key),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Augmented Chat Endpoint.
    1. Extracts the last user message in thread history.
    2. Recalls matching long-term memories semantically.
    3. Synthesizes a system prompt with injected context.
    4. Completes the prompt via OpenAI completions or a structural dev demo return.
    """
    # 1. Locate the last message to run semantic query search
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conversation history must contain at least one message from the 'user'."
        )
        
    last_query = user_messages[-1].content
    
    # 2. Recalls long-term semantic context internally
    logger.info(f"Recalling memories for augmented chat: '{last_query}'...")
    recall_req = MemoryRecallRequest(
        query=last_query,
        project_id=request.project_id,
        namespace=request.namespace,
        top_k=5
    )
    
    recall_res = await recall_memories(request=recall_req, api_key=api_key, db=db)
    context_block = recall_res.context_block
    
    # 3. Formulate system prompt injection block
    system_prompt = (
        "You are a helpful AI assistant. You have access to the following persistent, "
        "long-term semantic memories relating to the current workspace and project:\n\n"
        f"{context_block}\n\n"
        "Use this retrieved knowledge to guide your response. Reference coding standards, "
        "architecture choices, or past decisions directly if applicable. Keep responses structured."
    )
    
    # 4. Check for mock developer pipeline
    is_placeholder_key = "placeholder" in settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY
    if is_placeholder_key:
        logger.info("Executing local augmented chat mock response...")
        mock_response = (
            f"[UAMS AUGMENTED CHAT MOCK MODE]\n\n"
            f"I have received your request. In production, I would query OpenAI using the following "
            f"injected context and chat history:\n\n"
            f"--- INJECTED SYSTEM PROMPT ---\n{system_prompt}\n"
            f"-----------------------------\n\n"
            f"User Query: '{last_query}'"
        )
        return ChatResponse(response=mock_response)
        
    # 5. Call OpenAI ChatCompletions API
    logger.info("Routing augmented prompt to OpenAI API...")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepend our custom system prompt with injected context
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages:
        api_messages.append({"role": msg.role, "content": msg.content})
        
    payload = {
        "model": "gpt-4o-mini", # Standard lightweight, high-speed production model
        "messages": api_messages,
        "temperature": request.temperature
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            llm_text = data["choices"][0]["message"]["content"]
            return ChatResponse(response=llm_text)
            
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenAI Chat API HTTP error: {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate completions response from remote LLM provider."
        )
    except Exception as e:
        logger.error(f"Unexpected crash during chat augmentation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal handler exception during LLM completions routing."
        )
