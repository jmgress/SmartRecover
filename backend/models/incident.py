from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, List
from datetime import datetime
from backend.utils.categorization import CATEGORIES, DEFAULT_CATEGORY

IncidentCategory = Literal[
    "Database",
    "Application",
    "Infrastructure",
    "Network",
    "Security",
    "Storage",
    "Monitoring",
    "Cache",
    "Payments",
    "API",
]
RiskLevel = Literal["low", "medium", "high"]
IncidentSeverity = Literal["low", "medium", "high", "critical"]


class Incident(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    affected_services: List[str] = []
    assignee: Optional[str] = None
    category: Optional[IncidentCategory] = None


class IncidentQuery(BaseModel):
    incident_id: str
    user_query: str


class FeedbackRequest(BaseModel):
    """An incident responder's assessment of a resolution."""
    incident_id: str
    rating: Literal["helpful", "not_helpful"]
    comment: Optional[str] = Field(default=None, max_length=2000)


class FeedbackRecord(FeedbackRequest):
    """A persisted resolution feedback entry."""
    id: str
    created_at: datetime


class ResolutionDraftResponse(BaseModel):
    """An AI-generated first draft of an incident resolution."""
    incident_id: str
    draft: str
    source: str = "resolution_agent"


class SubmitResolutionRequest(BaseModel):
    """A user-submitted resolution for an incident."""
    resolution_text: str = Field(min_length=1, max_length=10000)


class ResolutionGrade(BaseModel):
    """AI assessment of a submitted resolution against recorded incident data."""
    score: float = Field(ge=0, le=1)
    passed: bool
    threshold: float = Field(ge=0, le=1)
    feedback: str
    issues: List[str] = []


class ResolutionRecord(BaseModel):
    """A persisted, accepted incident resolution."""
    id: str
    incident_id: str
    resolution_text: str
    grade: ResolutionGrade
    created_at: datetime


class SubmitResolutionResponse(BaseModel):
    """Result of submitting a resolution: the grade, plus the saved record when it passed."""
    incident_id: str
    grade: ResolutionGrade
    record: Optional[ResolutionRecord] = None


class TeamRecommendation(BaseModel):
    """A team recommended for involvement in resolving an incident."""
    team: str
    reasons: List[str] = []
    sources: List[str] = []


class SuggestedFix(BaseModel):
    """The most likely fix, highlighted so responders can act without digesting all agent results."""
    id: str
    title: str
    description: str
    script: str
    risk_level: RiskLevel
    estimated_duration: Optional[str] = None
    prerequisites: List[str] = []
    confidence_score: float = Field(ge=0, le=1)
    rationale: str
    source: str = "remediation_engine"


class AutomationDecision(BaseModel):
    automated: bool = False
    reason: str
    category: Optional[IncidentCategory] = None
    threshold: Optional[float] = Field(default=None, ge=0, le=1)
    incident_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    suggested_fix_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    risk_level: Optional[RiskLevel] = None
    severity: Optional[IncidentSeverity] = None
    suggested_fix_id: Optional[str] = None
    audit_record_id: Optional[str] = None


class AgentResponse(BaseModel):
    incident_id: str
    resolution_steps: List[str]
    related_knowledge: List[str]
    correlated_changes: List[str]
    summary: str
    confidence: float = Field(ge=0, le=1)
    recommended_teams: List[TeamRecommendation] = []
    suggested_fix: Optional[SuggestedFix] = None
    automation: Optional[AutomationDecision] = None
    automation_decision: AutomationDecision = Field(
        default_factory=lambda: AutomationDecision(
            automated=False,
            reason="automation not evaluated",
        )
    )


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


class MTTRBreakdown(BaseModel):
    """MTTR statistics for a single group (severity or category)."""
    label: str
    resolved_count: int
    mean_seconds: float
    mean_display: str


class MTTRMetricsResponse(BaseModel):
    """Response containing mean-time-to-resolution metrics."""
    overall_mean_seconds: Optional[float] = None
    overall_mean_display: Optional[str] = None
    resolved_count: int
    total_incidents: int
    by_severity: List[MTTRBreakdown]
    by_category: List[MTTRBreakdown]


class CategoryAutomationRule(BaseModel):
    category: IncidentCategory
    enabled: bool = False
    threshold: float = Field(default=0.75, ge=0, le=1)
    max_risk_level: RiskLevel = "low"
    max_severity: IncidentSeverity = "medium"


class AutomationAuditRecord(BaseModel):
    id: str
    incident_id: str
    automated: bool
    reason: str
    category: Optional[IncidentCategory] = None
    threshold: Optional[float] = Field(default=None, ge=0, le=1)
    incident_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    suggested_fix_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    risk_level: Optional[RiskLevel] = None
    severity: Optional[IncidentSeverity] = None
    suggested_fix_id: Optional[str] = None
    created_at: datetime


class AutomationConfig(BaseModel):
    global_enabled: bool = True
    rules: List[CategoryAutomationRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_categories(self):
        categories = [rule.category for rule in self.rules]
        if len(categories) != len(set(categories)):
            raise ValueError("Automation rules must have unique categories")
        return self


class UpdateAutomationConfigRequest(AutomationConfig):
    pass


class AutomationConfigResponse(AutomationConfig):
    recent_audit: List[AutomationAuditRecord] = Field(default_factory=list)


class PromptLog(BaseModel):
    """A log entry for an LLM prompt."""
    id: str
    incident_id: str
    timestamp: datetime
    prompt_type: str  # 'synthesis' or 'chat'
    system_prompt: str
    user_message: str
    conversation_history: Optional[List[ChatMessage]] = []
    context_summary: Optional[str] = None  # Brief summary of RAG data included


class PromptLogsResponse(BaseModel):
    """Response containing prompt logs."""
    logs: List[PromptLog]
    total_count: int
