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
