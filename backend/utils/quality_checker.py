"""
Quality checker for ServiceNow tickets.

This module provides functionality to assess the quality of ServiceNow tickets
based on completeness of description and resolution fields.
"""

from typing import Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class QualityLevel:
    """Quality level constants."""

    GOOD = "good"
    WARNING = "warning"
    POOR = "poor"


def calculate_ticket_quality(ticket: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate quality score for a single ServiceNow ticket.

    Quality is assessed based on:
    - Presence and length of description field
    - Presence and length of resolution field

    Args:
        ticket: Dictionary containing ticket data with optional 'description' and 'resolution' fields

    Returns:
        Dictionary with quality metrics:
        - score: Float between 0.0 and 1.0
        - level: Quality level (good/warning/poor)
        - issues: List of quality issues found
        - details: Detailed breakdown of scoring
    """
    score = 0.0
    issues = []
    details = {}

    # Check description (50% of score)
    description = ticket.get("description", "").strip()
    if not description:
        issues.append("Missing description")
        details["description_score"] = 0.0
    elif len(description) < 20:
        issues.append("Description too short (less than 20 characters)")
        details["description_score"] = 0.25
        score += 0.25
    elif len(description) < 50:
        details["description_score"] = 0.35
        score += 0.35
    else:
        details["description_score"] = 0.5
        score += 0.5

    # Check resolution (50% of score)
    resolution = ticket.get("resolution", "").strip()
    if not resolution:
        issues.append("Missing resolution")
        details["resolution_score"] = 0.0
    elif len(resolution) < 20:
        issues.append("Resolution too short (less than 20 characters)")
        details["resolution_score"] = 0.25
        score += 0.25
    elif len(resolution) < 50:
        details["resolution_score"] = 0.35
        score += 0.35
    else:
        details["resolution_score"] = 0.5
        score += 0.5

    # Determine quality level
    if score >= 0.8:
        level = QualityLevel.GOOD
    elif score >= 0.5:
        level = QualityLevel.WARNING
    else:
        level = QualityLevel.POOR

    logger.debug(
        f"Ticket {ticket.get('ticket_id')} quality: score={score:.2f}, level={level}"
    )

    return {
        "score": round(score, 2),
        "level": level,
        "issues": issues,
        "details": details,
    }


def calculate_tickets_quality(tickets: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate quality metrics for a list of tickets.

    Args:
        tickets: List of ticket dictionaries

    Returns:
        Dictionary with aggregate quality metrics:
        - average_score: Average quality score across all tickets
        - overall_level: Overall quality level
        - ticket_qualities: List of individual ticket quality assessments
        - summary: Summary statistics
    """
    if not tickets:
        logger.debug("No tickets to assess quality")
        return {
            "average_score": 0.0,
            "overall_level": QualityLevel.POOR,
            "ticket_qualities": [],
            "summary": {
                "total_tickets": 0,
                "good_count": 0,
                "warning_count": 0,
                "poor_count": 0,
            },
        }

    ticket_qualities = []
    total_score = 0.0
    good_count = 0
    warning_count = 0
    poor_count = 0

    for ticket in tickets:
        quality = calculate_ticket_quality(ticket)

        # Add ticket identifier to quality result
        quality["ticket_id"] = ticket.get("ticket_id", "unknown")
        quality["ticket_type"] = ticket.get("type", "unknown")

        ticket_qualities.append(quality)
        total_score += quality["score"]

        # Count by level
        if quality["level"] == QualityLevel.GOOD:
            good_count += 1
        elif quality["level"] == QualityLevel.WARNING:
            warning_count += 1
        else:
            poor_count += 1

    # Calculate average score
    average_score = total_score / len(tickets)

    # Determine overall level based on average score
    if average_score >= 0.8:
        overall_level = QualityLevel.GOOD
    elif average_score >= 0.5:
        overall_level = QualityLevel.WARNING
    else:
        overall_level = QualityLevel.POOR

    logger.info(
        f"Quality assessment complete: {len(tickets)} tickets, "
        f"avg score={average_score:.2f}, level={overall_level}"
    )

    return {
        "average_score": round(average_score, 2),
        "overall_level": overall_level,
        "ticket_qualities": ticket_qualities,
        "summary": {
            "total_tickets": len(tickets),
            "good_count": good_count,
            "warning_count": warning_count,
            "poor_count": poor_count,
        },
    }


def assess_similar_incidents_quality(
    similar_incidents: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Assess quality of similar incidents from ServiceNow results.

    This is a convenience wrapper for calculate_tickets_quality that focuses
    on similar_incident type tickets.

    Args:
        similar_incidents: List of similar incident tickets

    Returns:
        Quality assessment dictionary
    """
    # Filter to only similar_incident types
    similar_incident_tickets = [
        ticket
        for ticket in similar_incidents
        if ticket.get("type") == "similar_incident"
    ]

    return calculate_tickets_quality(similar_incident_tickets)
