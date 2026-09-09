"""Pure automation gate logic for simulated auto-remediation decisions."""

from typing import Any, Dict, Optional

from backend.models.automation import AutomationRules
from backend.models.incident import AutomationDecision


_RISK_ORDER = {"low": 0, "medium": 1, "high": 2}
_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def evaluate_automation(
    incident: Dict[str, Any],
    overall_confidence: Optional[float],
    suggested_fix: Optional[Dict[str, Any]],
    rules: AutomationRules,
) -> AutomationDecision:
    """Deny-by-default decision for simulated automation eligibility."""
    category = incident.get("category") or None
    severity = ((incident.get("severity") or "").lower() or None)

    fix = suggested_fix if isinstance(suggested_fix, dict) else None
    fix_confidence = fix.get("confidence_score") if fix else None
    risk_level = fix.get("risk_level") if fix else None
    fix_id = fix.get("id") if fix else None

    rule = rules.rules.get(category) if category else None
    reasons = []

    if not rules.global_enabled:
        reasons.append("global automation kill switch is off")
    if not category:
        reasons.append("incident category is unavailable")
    if not fix:
        reasons.append("no suggested fix present")

    if category:
        if rule is None:
            reasons.append(f"no automation rule configured for category '{category}'")
        elif not rule.enabled:
            reasons.append(f"automation rule for category '{category}' is disabled")

    if rule and rule.enabled:
        if overall_confidence is None or overall_confidence < rule.confidence_threshold:
            reasons.append(
                f"overall confidence below threshold ({overall_confidence!r} < {rule.confidence_threshold})"
            )
        if fix_confidence is None or fix_confidence < rule.min_fix_confidence:
            reasons.append(
                f"fix confidence below minimum ({fix_confidence!r} < {rule.min_fix_confidence})"
            )
        if risk_level is None:
            reasons.append("fix risk level is unavailable")
        elif _RISK_ORDER.get(risk_level, 99) > _RISK_ORDER.get(rule.max_risk_level, -1):
            reasons.append(
                f"fix risk level '{risk_level}' exceeds max '{rule.max_risk_level}'"
            )
        if severity is None:
            reasons.append("incident severity is unavailable")
        elif _SEVERITY_ORDER.get(severity, 99) > _SEVERITY_ORDER.get(rule.max_severity, -1):
            reasons.append(
                f"incident severity '{severity}' exceeds max '{rule.max_severity}'"
            )

    automated = len(reasons) == 0
    reason = (
        "auto-remediation simulated and audited"
        if automated
        else "; ".join(reasons)
    )
    return AutomationDecision(
        automated=automated,
        reason=reason,
        category=category,
        threshold=(rule.confidence_threshold if rule else None),
        incident_confidence=overall_confidence,
        suggested_fix_confidence=fix_confidence,
        risk_level=risk_level,
        severity=severity,
        suggested_fix_id=fix_id,
    )
