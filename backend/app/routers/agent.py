"""
Agent Router - FastAPI endpoints for Claude Opus 4.5 agent.

Provides:
- POST /chat - Send message and get response (with tool calling)
- GET /chat/stream - SSE streaming endpoint for real-time responses
- GET /history/{session_id} - Get conversation history
- DELETE /session/{session_id} - Clear/delete session
- GET /tools - List available tools
- GET /status - Get agent status
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentHistoryResponse,
    AgentHistoryMessage,
    AgentClearResponse,
    AgentToolsResponse,
    AgentToolInfo,
    AgentStatusResponse,
    ToolCall
)
from ..services.agent_service import get_agent_service
from ..config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])


def verify_api_key_param(api_key: Optional[str]) -> bool:
    """
    Verify API key from query parameter.
    Used for SSE endpoints where headers aren't available.
    Returns True if valid or if auth is disabled.
    """
    settings = get_settings()
    
    # If no API key configured, auth is disabled
    if not settings.api_key:
        return True
    
    # Check the provided key
    return api_key == settings.api_key


@router.post("/chat", response_model=AgentChatResponse)
async def chat(request: AgentChatRequest):
    """
    Send a message to the agent and receive a response.
    
    The agent will:
    1. Process your message
    2. Call any necessary tools (generate scripts, images, etc.)
    3. Return a comprehensive response
    
    Provide session_id to continue a conversation.
    """
    try:
        service = get_agent_service()
        result = await service.chat(
            message=request.message,
            session_id=request.session_id
        )
        
        return AgentChatResponse(
            session_id=result["session_id"],
            response=result["response"],
            tool_calls=[
                ToolCall(
                    tool_name=tc["tool_name"],
                    tool_input=tc["tool_input"],
                    result=tc["result"],
                    success=tc["success"]
                )
                for tc in result.get("tool_calls", [])
            ],
            iterations=result.get("iterations", 0)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.get("/chat/stream")
async def chat_stream(
    message: str = Query(..., description="User message"),
    session_id: Optional[str] = Query(None, description="Session ID for continuity"),
    api_key: Optional[str] = Query(None, description="API key (required if auth enabled)")
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    
    Note: API key must be passed as query param since EventSource doesn't support headers.
    
    Events:
    - session: {"session_id": "..."} - Session info
    - text: {"text": "..."} - Streaming text chunks
    - tool_start: {"tool_name": "...", "tool_input": {...}} - Tool execution starting
    - tool_result: {"tool_name": "...", "result": {...}, "success": bool} - Tool completed
    - done: {"iterations": N, "tool_count": M} - Response complete
    - error: {"message": "..."} - Error occurred
    """
    # Verify API key for SSE endpoint
    if not verify_api_key_param(api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        service = get_agent_service()
        
        async def event_generator():
            async for event in service.chat_stream(message, session_id):
                event_type = event.pop("type", "message")
                yield {
                    "event": event_type,
                    "data": json.dumps(event)
                }
        
        return EventSourceResponse(event_generator())
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.get("/history/{session_id}", response_model=AgentHistoryResponse)
async def get_history(session_id: str):
    """
    Get the conversation history for a session.
    """
    try:
        service = get_agent_service()
        messages = service.get_history(session_id)
        
        if not messages:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return AgentHistoryResponse(
            session_id=session_id,
            messages=[
                AgentHistoryMessage(
                    role=msg["role"],
                    content=msg["content"],
                    timestamp=msg.get("timestamp"),
                    tool_calls=[
                        ToolCall(**tc) for tc in msg.get("tool_calls", [])
                    ] if msg.get("tool_calls") else None
                )
                for msg in messages
            ],
            message_count=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}", response_model=AgentClearResponse)
async def clear_session(session_id: str):
    """
    Clear a session's conversation history.
    """
    try:
        service = get_agent_service()
        success = service.clear_session(session_id)
        
        return AgentClearResponse(
            session_id=session_id,
            cleared=success,
            message="Session cleared" if success else "Session not found"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools", response_model=AgentToolsResponse)
async def list_tools():
    """
    List all available tools the agent can use.
    """
    try:
        service = get_agent_service()
        tools_info = service.get_tools_info()
        
        # Get unique categories
        categories = list(set(t.get("category", "other") for t in tools_info))
        
        return AgentToolsResponse(
            tools=[
                AgentToolInfo(
                    name=t["name"],
                    description=t["description"],
                    parameters=t["parameters"],
                    category=t["category"]
                )
                for t in tools_info
            ],
            total=len(tools_info),
            categories=sorted(categories)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=AgentStatusResponse)
async def get_status():
    """
    Get the agent's current status and configuration.
    """
    try:
        service = get_agent_service()
        status = service.get_status()
        
        return AgentStatusResponse(**status)
        
    except ValueError as e:
        # Agent not configured (no API key)
        raise HTTPException(
            status_code=503,
            detail=f"Agent not available: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
