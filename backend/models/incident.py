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
    excluded_at: Optional[datetime] = None
    reason: Optional[str] = None


class ExcludeItemRequest(BaseModel):
    """Request to exclude an item from chat context."""
    item_id: str
    item_type: str
    source: str
    reason: Optional[str] = None


class CategoryAccuracy(BaseModel):
    """Accuracy metrics for a specific category."""
    category: str
    total_items_returned: int
    total_items_excluded: int
    accuracy_score: float  # (total_items_returned - total_items_excluded) / total_items_returned


class AccuracyMetricsResponse(BaseModel):
    """Response containing accuracy metrics for all categories."""
    categories: List[CategoryAccuracy]
    overall_accuracy: float
    total_exclusions: int
    total_items_returned: int
