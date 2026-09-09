from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

from backend.utils.categorization import CATEGORIES


RiskLevel = Literal["low", "medium", "high"]
SeverityLevel = Literal["low", "medium", "high", "critical"]
AutomationMode = Literal["simulated"]


class CategoryAutomationRule(BaseModel):
    enabled: bool = False
    confidence_threshold: float = Field(default=0.85, ge=0, le=1)
    min_fix_confidence: float = Field(default=0.85, ge=0, le=1)
    max_risk_level: RiskLevel = "low"
    max_severity: SeverityLevel = "medium"


class AutomationRules(BaseModel):
    global_enabled: bool = False
    rules: Dict[str, CategoryAutomationRule] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_and_normalize_categories(self):
        unknown_categories = sorted(set(self.rules) - set(CATEGORIES))
        if unknown_categories:
            raise ValueError(
                f"Unknown automation categories: {', '.join(unknown_categories)}"
            )

        normalized_rules: Dict[str, CategoryAutomationRule] = {
            category: CategoryAutomationRule() for category in CATEGORIES
        }
        normalized_rules.update(self.rules)
        self.rules = normalized_rules
        return self


class AutomationDecision(BaseModel):
    automated: bool = False
    category: Optional[str] = None
    mode: AutomationMode = "simulated"
    reasons: List[str] = Field(default_factory=list)
    overall_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    fix_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    applied_rule: Optional[CategoryAutomationRule] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fix_id: Optional[str] = None


class AutomationAuditRecord(AutomationDecision):
    id: str
    incident_id: str
    fix_title: Optional[str] = None
    script: Optional[str] = None
