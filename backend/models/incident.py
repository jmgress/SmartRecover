from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Incident(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    affected_services: List[str] = []
    assignee: Optional[str] = None


class IncidentQuery(BaseModel):
    incident_id: str
    user_query: str


class AgentResponse(BaseModel):
    incident_id: str
    resolution_steps: List[str]
    related_knowledge: List[str]
    correlated_changes: List[str]
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
    conversation_history: List[ChatMessage] = []
    excluded_items: Optional[List[str]] = []


class ChatStreamChunk(BaseModel):
    """A chunk of streaming chat response."""
    type: str  # 'content', 'done', 'error'
    content: Optional[str] = None
    error: Optional[str] = None


class ExcludedItem(BaseModel):
    """An item that has been excluded from chat context."""
    item_id: str
    item_type: str  # 'incident', 'document', 'change', 'log', 'event', 'remediation'
    source: str  # 'servicenow', 'confluence', 'change_correlation', 'logs', 'events', 'remediation'


class ExcludeItemRequest(BaseModel):
    """Request to exclude an item from chat context."""
    item_id: str
    item_type: str
    source: str
