"""
Mock data loader for SmartRecover.

This module loads mock data from CSV files for testing and development.
CSV files are located in the backend/data/csv/ directory.

CSV File Formats:
- incidents.csv: id, title, description, severity, status, created_at, affected_services, assignee
- servicenow_tickets.csv: incident_id, ticket_id, type, resolution, description, source
- confluence_docs.csv: incident_id, doc_id, title, content
- change_correlations.csv: incident_id, change_id, description, deployed_at, correlation_score
"""

import contextlib
import csv
from datetime import datetime
from pathlib import Path
from typing import Any


class MockDataLoadError(Exception):
    """Exception raised when mock data fails to load."""
    pass


def _get_csv_dir() -> Path:
    """Get the path to the CSV data directory."""
    return Path(__file__).parent / "csv"


def _load_incidents() -> list[dict[str, Any]]:
    """
    Load incidents from CSV file.

    Returns:
        List of incident dictionaries

    Raises:
        MockDataLoadError: If CSV file is missing or malformed
    """
    csv_path = _get_csv_dir() / "incidents.csv"

    if not csv_path.exists():
        raise MockDataLoadError(f"Incidents CSV file not found: {csv_path}")

    try:
        incidents = []
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse affected_services from pipe-delimited string
                affected_services = row['affected_services'].split('|') if row['affected_services'] else []

                # Parse datetime
                created_at = datetime.fromisoformat(row['created_at'])

                # Handle optional assignee
                assignee = row['assignee'] if row['assignee'] else None

                # Handle optional updated_at (for backward compatibility)
                updated_at = None
                if 'updated_at' in row and row['updated_at']:
                    with contextlib.suppress(ValueError, TypeError):
                        updated_at = datetime.fromisoformat(row['updated_at'])

                incidents.append({
                    "id": row['id'],
                    "title": row['title'],
                    "description": row['description'],
                    "severity": row['severity'],
                    "status": row['status'],
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "affected_services": affected_services,
                    "assignee": assignee
                })

        return incidents
    except Exception as e:
        raise MockDataLoadError(f"Error loading incidents CSV: {str(e)}") from e


def _load_servicenow_tickets() -> dict[str, list[dict[str, Any]]]:
    """
    Load ServiceNow tickets from CSV file.

    Returns:
        Dictionary mapping incident_id to list of tickets

    Raises:
        MockDataLoadError: If CSV file is missing or malformed
    """
    csv_path = _get_csv_dir() / "servicenow_tickets.csv"

    if not csv_path.exists():
        raise MockDataLoadError(f"ServiceNow tickets CSV file not found: {csv_path}")

    try:
        tickets_by_incident = {}
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                incident_id = row['incident_id']

                if incident_id not in tickets_by_incident:
                    tickets_by_incident[incident_id] = []

                ticket = {
                    "ticket_id": row['ticket_id'],
                    "type": row['type'],
                    "source": row['source']
                }

                # Add optional fields
                if row['resolution']:
                    ticket['resolution'] = row['resolution']
                if row['description']:
                    ticket['description'] = row['description']

                tickets_by_incident[incident_id].append(ticket)

        return tickets_by_incident
    except Exception as e:
        raise MockDataLoadError(f"Error loading ServiceNow tickets CSV: {str(e)}") from e


def _load_confluence_docs() -> dict[str, list[dict[str, Any]]]:
    """
    Load Confluence documents from CSV file.

    Returns:
        Dictionary mapping incident_id to list of documents

    Raises:
        MockDataLoadError: If CSV file is missing or malformed
    """
    csv_path = _get_csv_dir() / "confluence_docs.csv"

    if not csv_path.exists():
        raise MockDataLoadError(f"Confluence docs CSV file not found: {csv_path}")

    try:
        docs_by_incident = {}
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                incident_id = row['incident_id']

                if incident_id not in docs_by_incident:
                    docs_by_incident[incident_id] = []

                docs_by_incident[incident_id].append({
                    "doc_id": row['doc_id'],
                    "title": row['title'],
                    "content": row['content']
                })

        return docs_by_incident
    except Exception as e:
        raise MockDataLoadError(f"Error loading Confluence docs CSV: {str(e)}") from e


def _load_change_correlations() -> dict[str, list[dict[str, Any]]]:
    """
    Load change correlations from CSV file.

    Returns:
        Dictionary mapping incident_id to list of changes

    Raises:
        MockDataLoadError: If CSV file is missing or malformed
    """
    csv_path = _get_csv_dir() / "change_correlations.csv"

    if not csv_path.exists():
        raise MockDataLoadError(f"Change correlations CSV file not found: {csv_path}")

    try:
        correlations_by_incident = {}
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                incident_id = row['incident_id']

                if incident_id not in correlations_by_incident:
                    correlations_by_incident[incident_id] = []

                correlations_by_incident[incident_id].append({
                    "change_id": row['change_id'],
                    "description": row['description'],
                    "deployed_at": row['deployed_at'],
                    "correlation_score": float(row['correlation_score'])
                })

        return correlations_by_incident
    except Exception as e:
        raise MockDataLoadError(f"Error loading change correlations CSV: {str(e)}") from e


# Load all mock data at module import time
try:
    MOCK_INCIDENTS = _load_incidents()
    MOCK_SERVICENOW_TICKETS = _load_servicenow_tickets()
    MOCK_CONFLUENCE_DOCS = _load_confluence_docs()
    MOCK_CHANGE_CORRELATIONS = _load_change_correlations()
except MockDataLoadError as e:
    # Log error and use empty data structures to prevent application crash
    import sys
    print(f"WARNING: Failed to load mock data: {str(e)}", file=sys.stderr)
    print("Using empty mock data structures.", file=sys.stderr)
    MOCK_INCIDENTS = []
    MOCK_SERVICENOW_TICKETS = {}
    MOCK_CONFLUENCE_DOCS = {}
    MOCK_CHANGE_CORRELATIONS = {}


def _save_incidents(incidents: list[dict[str, Any]]) -> None:
    """
    Save incidents to CSV file.

    Args:
        incidents: List of incident dictionaries

    Raises:
        MockDataLoadError: If CSV file cannot be written
    """
    csv_path = _get_csv_dir() / "incidents.csv"

    try:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['id', 'title', 'description', 'severity', 'status',
                         'created_at', 'updated_at', 'affected_services', 'assignee']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for incident in incidents:
                # Convert affected_services list to pipe-delimited string
                affected_services_str = '|'.join(incident['affected_services']) if incident['affected_services'] else ''

                # Convert datetime to ISO format string
                created_at_str = incident['created_at'].isoformat() if isinstance(incident['created_at'], datetime) else incident['created_at']

                # Convert updated_at to ISO format string if present
                updated_at_str = ''
                if incident.get('updated_at'):
                    updated_at_str = incident['updated_at'].isoformat() if isinstance(incident['updated_at'], datetime) else incident['updated_at']

                # Handle optional assignee
                assignee_str = incident['assignee'] if incident['assignee'] else ''

                writer.writerow({
                    'id': incident['id'],
                    'title': incident['title'],
                    'description': incident['description'],
                    'severity': incident['severity'],
                    'status': incident['status'],
                    'created_at': created_at_str,
                    'updated_at': updated_at_str,
                    'affected_services': affected_services_str,
                    'assignee': assignee_str
                })
    except Exception as e:
        raise MockDataLoadError(f"Error saving incidents CSV: {str(e)}") from e


def update_incident_status(incident_id: str, new_status: str) -> bool:
    """
    Update the status of an incident and persist to CSV.

    Args:
        incident_id: The ID of the incident to update
        new_status: The new status value

    Returns:
        True if the incident was found and updated, False otherwise

    Raises:
        MockDataLoadError: If CSV file cannot be written
    """
    global MOCK_INCIDENTS

    # Find and update the incident in memory
    incident_found = False
    for incident in MOCK_INCIDENTS:
        if incident['id'] == incident_id:
            incident['status'] = new_status
            incident['updated_at'] = datetime.now()
            incident_found = True
            break

    if not incident_found:
        return False

    # Persist to CSV
    _save_incidents(MOCK_INCIDENTS)

    return True


def reload_mock_data():
    """
    Reload mock data from CSV files.

    This utility function can be used to reload data without restarting the server.

    Raises:
        MockDataLoadError: If any CSV file is missing or malformed
    """
    global MOCK_INCIDENTS, MOCK_SERVICENOW_TICKETS, MOCK_CONFLUENCE_DOCS, MOCK_CHANGE_CORRELATIONS

    MOCK_INCIDENTS = _load_incidents()
    MOCK_SERVICENOW_TICKETS = _load_servicenow_tickets()
    MOCK_CONFLUENCE_DOCS = _load_confluence_docs()
    MOCK_CHANGE_CORRELATIONS = _load_change_correlations()
