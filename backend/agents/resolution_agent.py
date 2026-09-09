"""
Resolution Agent for AI-drafted and AI-graded incident resolutions.

Drafts a first-pass resolution from recorded incident data and grades
user-submitted resolutions so low-effort text (e.g. just "resolved")
cannot be recorded as the resolution.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import config_manager
from backend.data import mock_data
from backend.llm.llm_manager import get_llm
from backend.models.incident import ResolutionGrade
from backend.utils.logger import get_logger, trace_async_execution

logger = get_logger(__name__)

# Low-effort phrases that are never acceptable as a full resolution.
GENERIC_RESOLUTION_PHRASES = {
    "resolved",
    "fixed",
    "done",
    "closed",
    "complete",
    "completed",
    "issue resolved",
    "issue fixed",
    "problem solved",
    "problem fixed",
    "it works now",
    "works now",
    "fixed it",
    "resolved it",
    "n/a",
    "na",
    "ok",
    "okay",
    "solved",
}

_WORD_RE = re.compile(r"[a-z0-9]+")

_STOP_WORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "was",
    "is", "are", "were", "be", "been", "this", "that", "with", "by", "at",
    "we", "it", "its", "as", "from", "after", "before",
}


class ResolutionAgent:
    """Agent that drafts and grades incident resolutions."""

    def __init__(self):
        self.name = "resolution_agent"
        self._llm = None
        logger.debug(f"Initialized {self.name}")

    @property
    def llm(self):
        """Lazily create the LLM so drafting/grading fallbacks work without one."""
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    @trace_async_execution
    async def query(self, incident_id: str, context: str) -> Dict[str, Any]:
        """Standard agent contract: return a drafted resolution for the incident."""
        draft = await self.draft_resolution(incident_id)
        return {
            "source": self.name,
            "incident_id": incident_id,
            "draft": draft,
        }

    @trace_async_execution
    async def draft_resolution(self, incident_id: str) -> str:
        """Generate a first-draft resolution from recorded incident data."""
        incident, tickets = self._gather_incident_context(incident_id)
        context_text = self._format_context(incident, tickets)

        system_prompt = (
            "You are an experienced incident responder writing the official resolution "
            "record for an incident. Using only the recorded data provided, write a "
            "concise resolution (3-6 sentences) that states the root cause, the actions "
            "taken to resolve it, and any verification or follow-up performed. Write in "
            "past tense. Do not invent details that are not supported by the data; where "
            "the data is incomplete, leave a bracketed placeholder like [describe fix applied]."
        )
        human_prompt = f"Recorded incident data:\n\n{context_text}\n\nWrite the resolution draft."

        try:
            response = await self.llm.ainvoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
            )
            draft = (response.content or "").strip()
            if draft:
                return draft
            logger.warning("LLM returned an empty resolution draft for %s", incident_id)
        except Exception as exc:
            logger.warning("LLM resolution draft failed for %s: %s", incident_id, exc)

        return self._fallback_draft(incident, tickets)

    @trace_async_execution
    async def grade_resolution(self, incident_id: str, resolution_text: str) -> ResolutionGrade:
        """Grade a user-submitted resolution against recorded incident data."""
        resolution_config = config_manager.get_resolution_config()
        threshold = resolution_config.quality_threshold

        # Deterministic junk checks run first so obvious low-effort text is
        # always rejected, even when no LLM is available.
        heuristic_score, issues = self._heuristic_check(
            incident_id, resolution_text, resolution_config.min_length
        )
        if issues:
            return ResolutionGrade(
                score=heuristic_score,
                passed=False,
                threshold=threshold,
                feedback=(
                    "This resolution does not meet the quality bar. "
                    "Describe the root cause, the specific actions taken, and how the fix was verified."
                ),
                issues=issues,
            )

        llm_grade = await self._llm_grade(incident_id, resolution_text)
        if llm_grade is not None:
            score, feedback, llm_issues = llm_grade
            return ResolutionGrade(
                score=score,
                passed=score >= threshold,
                threshold=threshold,
                feedback=feedback,
                issues=llm_issues,
            )

        # LLM unavailable: the text already passed the heuristic gate.
        return ResolutionGrade(
            score=heuristic_score,
            passed=heuristic_score >= threshold,
            threshold=threshold,
            feedback="Graded heuristically (LLM unavailable): the resolution is sufficiently descriptive.",
            issues=[],
        )

    def _heuristic_check(
        self, incident_id: str, resolution_text: str, min_length: int
    ) -> Tuple[float, List[str]]:
        """Deterministic quality checks. Returns (score, issues); issues means rejection."""
        issues: List[str] = []
        text = resolution_text.strip()
        normalized = re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()

        if normalized in GENERIC_RESOLUTION_PHRASES:
            issues.append(
                f'"{text}" is a generic phrase, not a resolution. Describe what caused the incident and what was done to fix it.'
            )
            return 0.05, issues

        if len(text) < min_length:
            issues.append(
                f"The resolution is too short ({len(text)} characters; minimum {min_length}). "
                "Include the root cause, the fix applied, and verification."
            )
            return 0.1, issues

        words = _WORD_RE.findall(normalized)
        meaningful_words = [w for w in words if w not in _STOP_WORDS]
        if len(set(meaningful_words)) < 5:
            issues.append(
                "The resolution lacks descriptive detail. Explain the root cause, actions taken, and verification steps."
            )
            return 0.2, issues

        incident, tickets = self._gather_incident_context(incident_id)
        context_words = set(
            _WORD_RE.findall(self._format_context(incident, tickets).lower())
        ) - _STOP_WORDS
        overlap = set(meaningful_words) & context_words
        if context_words and not overlap:
            issues.append(
                "The resolution does not reference anything recorded for this incident "
                "(affected services, symptoms, or changes). Tie the resolution to what actually happened."
            )
            return 0.3, issues

        # Passed all deterministic checks; score reflects basic descriptiveness.
        base_score = min(1.0, 0.55 + 0.05 * min(len(set(meaningful_words)), 8) + 0.05 * min(len(overlap), 2))
        return base_score, []

    async def _llm_grade(
        self, incident_id: str, resolution_text: str
    ) -> Optional[Tuple[float, str, List[str]]]:
        """Ask the LLM to grade the resolution. Returns None when unavailable."""
        incident, tickets = self._gather_incident_context(incident_id)
        context_text = self._format_context(incident, tickets)

        system_prompt = (
            "You are a strict incident management quality reviewer. Grade the submitted "
            "resolution against the recorded incident data. A good resolution states the "
            "root cause, the concrete actions taken, and verification, and is consistent "
            "with the recorded data. Vague text like 'resolved' or 'fixed' must score near 0.\n\n"
            "Respond with only a JSON object: "
            '{"score": <float 0-1>, "feedback": "<one or two sentences of actionable feedback>", '
            '"issues": ["<specific problem>", ...]}. Use an empty issues list when the resolution is good.'
        )
        human_prompt = (
            f"Recorded incident data:\n\n{context_text}\n\n"
            f"Submitted resolution:\n\n{resolution_text}\n\nGrade it."
        )

        try:
            response = await self.llm.ainvoke(
                [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
            )
            return self._parse_grade_response(response.content or "")
        except Exception as exc:
            logger.warning("LLM resolution grading failed for %s: %s", incident_id, exc)
            return None

    def _parse_grade_response(self, content: str) -> Optional[Tuple[float, str, List[str]]]:
        """Parse the LLM grading JSON, tolerating surrounding prose/code fences."""
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            logger.warning("Could not find JSON in LLM grading response")
            return None
        try:
            parsed = json.loads(match.group(0))
            score = float(parsed["score"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            logger.warning("Could not parse LLM grading response")
            return None
        score = max(0.0, min(1.0, score))
        feedback = str(parsed.get("feedback", "")).strip() or "No feedback provided."
        raw_issues = parsed.get("issues", [])
        issues = [str(issue) for issue in raw_issues] if isinstance(raw_issues, list) else []
        return score, feedback, issues

    def _gather_incident_context(
        self, incident_id: str
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Collect recorded data for the incident from the mock data stores."""
        incident: Dict[str, Any] = {}
        for candidate in mock_data.MOCK_INCIDENTS:
            if candidate.get("id") == incident_id:
                incident = candidate
                break
        tickets = mock_data.MOCK_SERVICENOW_TICKETS.get(incident_id, [])
        return incident, tickets

    def _format_context(
        self, incident: Dict[str, Any], tickets: List[Dict[str, Any]]
    ) -> str:
        """Format recorded incident data as prompt-ready text."""
        lines = [
            f"Incident ID: {incident.get('id', 'unknown')}",
            f"Title: {incident.get('title', 'unknown')}",
            f"Description: {incident.get('description', 'unknown')}",
            f"Severity: {incident.get('severity', 'unknown')}",
            f"Status: {incident.get('status', 'unknown')}",
            f"Affected services: {', '.join(incident.get('affected_services', [])) or 'none recorded'}",
        ]
        if tickets:
            lines.append("\nRelated tickets:")
            for ticket in tickets[:5]:
                lines.append(
                    f"- [{ticket.get('ticket_id', '?')}] {ticket.get('description', '')}"
                )
                if ticket.get("resolution"):
                    lines.append(f"  Prior resolution: {ticket['resolution']}")
        return "\n".join(lines)

    def _fallback_draft(
        self, incident: Dict[str, Any], tickets: List[Dict[str, Any]]
    ) -> str:
        """Template-based draft used when the LLM is unavailable."""
        title = incident.get("title", "the incident")
        services = ", ".join(incident.get("affected_services", [])) or "the affected services"
        prior = next(
            (ticket["resolution"] for ticket in tickets if ticket.get("resolution")),
            None,
        )
        draft = (
            f"Root cause: [describe the root cause of \"{title}\"]. "
            f"Actions taken: [describe the fix applied to {services}]. "
            f"Verification: [describe how recovery of {services} was confirmed]."
        )
        if prior:
            draft += f" Reference from a similar prior ticket: {prior}"
        return draft


# Singleton used by API routes.
resolution_agent = ResolutionAgent()
