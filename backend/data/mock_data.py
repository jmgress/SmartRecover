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

import csv
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


class MockDataLoadError(Exception):
    """Exception raised when mock data fails to load."""
    pass


def _get_csv_dir() -> Path:
    """Get the path to the CSV data directory."""
    return Path(__file__).parent / "csv"


def _load_incidents() -> List[Dict[str, Any]]:
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
        with open(csv_path, 'r', encoding='utf-8') as f:
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
                    try:
                        updated_at = datetime.fromisoformat(row['updated_at'])
                    except (ValueError, TypeError):
                        pass
                
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


def _load_servicenow_tickets() -> Dict[str, List[Dict[str, Any]]]:
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
        with open(csv_path, 'r', encoding='utf-8') as f:
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


def _load_confluence_docs() -> Dict[str, List[Dict[str, Any]]]:
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
        with open(csv_path, 'r', encoding='utf-8') as f:
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



def _load_change_correlations() -> Dict[str, List[Dict[str, Any]]]:
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
        with open(csv_path, 'r', encoding='utf-8') as f:
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


def _save_incidents(incidents: List[Dict[str, Any]]) -> None:
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


def validate_servicenow_tickets() -> dict:
    """
    Validate ServiceNow tickets for data quality issues.
    
    Checks performed:
    - Ticket types are valid (similar_incident or related_change)
    - Ticket IDs are unique
    - Referenced incident IDs exist in MOCK_INCIDENTS
    - Resolution field is populated for similar_incident tickets
    - Description field is populated for related_change tickets
    - Source values are valid (servicenow or jira)
    
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "stats": {
                "total_tickets": int,
                "valid_tickets": int,
                "invalid_tickets": int
            }
        }
    """
    errors = []
    warnings = []
    ticket_ids_seen = set()
    valid_ticket_types = {'similar_incident', 'related_change'}
    valid_sources = {'servicenow', 'jira'}
    incident_ids = {inc['id'] for inc in MOCK_INCIDENTS}
    
    total_tickets = 0
    invalid_tickets = 0
    
    # Iterate through all tickets
    for incident_id, tickets in MOCK_SERVICENOW_TICKETS.items():
        for ticket in tickets:
            total_tickets += 1
            ticket_id = ticket.get('ticket_id', '')
            ticket_type = ticket.get('type', '')
            source = ticket.get('source', '')
            resolution = ticket.get('resolution', '')
            description = ticket.get('description', '')
            
            # Check if incident_id exists
            if incident_id not in incident_ids:
                errors.append(f"Ticket {ticket_id}: References non-existent incident {incident_id}")
                invalid_tickets += 1
            
            # Check for duplicate ticket IDs
            if ticket_id in ticket_ids_seen:
                errors.append(f"Ticket {ticket_id}: Duplicate ticket ID found")
                invalid_tickets += 1
            ticket_ids_seen.add(ticket_id)
            
            # Check if ticket type is valid
            if ticket_type not in valid_ticket_types:
                errors.append(f"Ticket {ticket_id}: Invalid type '{ticket_type}', must be one of {valid_ticket_types}")
                invalid_tickets += 1
            
            # Check if source is valid
            if source not in valid_sources:
                errors.append(f"Ticket {ticket_id}: Invalid source '{source}', must be one of {valid_sources}")
                invalid_tickets += 1
            
            # Type-specific validation
            if ticket_type == 'similar_incident':
                if not resolution:
                    warnings.append(f"Ticket {ticket_id}: Similar incident ticket missing resolution field")
                if description:
                    warnings.append(f"Ticket {ticket_id}: Similar incident ticket has description field (should be empty)")
            elif ticket_type == 'related_change':
                if not description:
                    warnings.append(f"Ticket {ticket_id}: Related change ticket missing description field")
                if resolution:
                    warnings.append(f"Ticket {ticket_id}: Related change ticket has resolution field (should be empty)")
    
    valid_tickets = total_tickets - invalid_tickets
    is_valid = len(errors) == 0
    
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "total_tickets": total_tickets,
            "valid_tickets": valid_tickets,
            "invalid_tickets": invalid_tickets
        }
    }


# Load all mock data at module import time
try:
    MOCK_INCIDENTS = _load_incidents()
    MOCK_SERVICENOW_TICKETS = _load_servicenow_tickets()
    MOCK_CONFLUENCE_DOCS = _load_confluence_docs()
    MOCK_CHANGE_CORRELATIONS = _load_change_correlations()
    
    # Validate ServiceNow tickets after loading
    validation_results = validate_servicenow_tickets()
    if validation_results['errors']:
        import sys
        print(f"ERROR: ServiceNow ticket validation failed with {len(validation_results['errors'])} error(s):", file=sys.stderr)
        for error in validation_results['errors']:
            print(f"  - {error}", file=sys.stderr)
    
    if validation_results['warnings']:
        import sys
        print(f"WARNING: ServiceNow ticket validation found {len(validation_results['warnings'])} warning(s):", file=sys.stderr)
        for warning in validation_results['warnings'][:5]:  # Only show first 5 warnings
            print(f"  - {warning}", file=sys.stderr)
        if len(validation_results['warnings']) > 5:
            print(f"  ... and {len(validation_results['warnings']) - 5} more warnings", file=sys.stderr)
    
except MockDataLoadError as e:
    # Log error and use empty data structures to prevent application crash
    import sys
    print(f"WARNING: Failed to load mock data: {str(e)}", file=sys.stderr)
    print("Using empty mock data structures.", file=sys.stderr)
    MOCK_INCIDENTS = []
    MOCK_SERVICENOW_TICKETS = {}
    MOCK_CONFLUENCE_DOCS = {}
    MOCK_CHANGE_CORRELATIONS = {}
