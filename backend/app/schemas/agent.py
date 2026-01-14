"""Pydantic schemas for the Claude Agent API."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    """Request to send a message to the agent."""
    message: str = Field(..., min_length=1, description="User message to the agent")
    session_id: Optional[str] = Field(
        default=None, 
        description="Session ID for conversation continuity. If not provided, a new session is created."
    )


class ToolCall(BaseModel):
    """A tool call made by the agent."""
    tool_name: str
    tool_input: Dict[str, Any]
    result: Dict[str, Any]
    success: bool


class AgentChatResponse(BaseModel):
    """Response from the agent."""
    session_id: str
    response: str = Field(..., description="Agent's text response")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tools called during this interaction")
    iterations: int = Field(default=0, description="Number of agentic loop iterations")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentHistoryMessage(BaseModel):
    """A message in the conversation history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    tool_calls: Optional[List[ToolCall]] = None


class AgentHistoryResponse(BaseModel):
    """Conversation history for a session."""
    session_id: str
    messages: List[AgentHistoryMessage]
    message_count: int


class AgentClearResponse(BaseModel):
    """Response after clearing a session."""
    session_id: str
    cleared: bool
    message: str


class AgentToolInfo(BaseModel):
    """Information about an available tool."""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str


class AgentToolsResponse(BaseModel):
    """List of all available tools."""
    tools: List[AgentToolInfo]
    total: int
    categories: List[str]


class AgentStatusResponse(BaseModel):
    """Agent status and configuration."""
    model: str
    max_tokens: int
    max_iterations: int
    active_sessions: int
    available_tools: int
