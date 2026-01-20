from datetime import datetime

from pydantic import BaseModel


class Incident(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    affected_services: list[str] = []
    assignee: str | None = None


class IncidentQuery(BaseModel):
    incident_id: str
    user_query: str


class AgentResponse(BaseModel):
    incident_id: str
    resolution_steps: list[str]
    related_knowledge: list[str]
    correlated_changes: list[str]
    summary: str
    confidence: float


class ChatMessage(BaseModel):
    """A chat message in the conversation."""

    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    """Request for interactive chat."""

    incident_id: str
    message: str
    conversation_history: list[ChatMessage] = []


class ChatStreamChunk(BaseModel):
    """A chunk of streaming chat response."""

    type: str  # 'content', 'done', 'error'
    content: str | None = None
    error: str | None = None
