# Mock Data CSV Files

This directory contains CSV files that provide mock data for SmartRecover's testing and development environments.

## Overview

Mock data is loaded from CSV files at application startup. This approach provides several benefits:
- **Easy editing**: Modify data using spreadsheet applications or text editors
- **Version control friendly**: CSV changes are easy to review in diffs
- **Non-technical accessibility**: Team members can modify test scenarios without Python knowledge
- **Flexibility**: Quick dataset swapping for different testing scenarios

## CSV File Formats

### incidents.csv

Contains mock incident records.

**Columns:**
- `id` (string): Unique incident identifier (e.g., "INC001")
- `title` (string): Brief incident title
- `description` (string): Detailed incident description
- `severity` (string): Severity level (e.g., "high", "medium", "low")
- `status` (string): Current status (e.g., "open", "investigating", "resolved")
- `created_at` (datetime): ISO 8601 timestamp (e.g., "2026-01-17T10:30:00")
- `affected_services` (string): Pipe-delimited list of services (e.g., "service1|service2")
- `assignee` (string): Assigned team or person (empty for unassigned)

**Example:**
```csv
id,title,description,severity,status,created_at,affected_services,assignee
INC001,Database connection timeout,Production database experiencing intermittent connection timeouts,high,open,2026-01-17T10:30:00,auth-service|user-service,ops-team
INC002,API response latency spike,Customer-facing API showing 5x increase in response times,medium,investigating,2026-01-17T12:00:00,api-gateway|order-service,
```

### servicenow_tickets.csv

Contains ServiceNow tickets and related records linked to incidents.

**Columns:**
- `incident_id` (string): Reference to incident ID
- `ticket_id` (string): Unique ticket identifier
- `type` (string): Ticket type ("similar_incident" or "related_change")
- `resolution` (string): Resolution description (for similar_incident types)
- `description` (string): Additional description (for related_change types)
- `source` (string): Source system (e.g., "servicenow", "jira")

**Example:**
```csv
incident_id,ticket_id,type,resolution,description,source
INC001,SNOW001,similar_incident,Increased connection pool size and added retry logic,,servicenow
INC001,SNOW002,related_change,,Database migration completed last week,servicenow
```

### confluence_docs.csv

Contains Confluence documentation and runbooks linked to incidents.

**Columns:**
- `incident_id` (string): Reference to incident ID
- `doc_id` (string): Unique document identifier
- `title` (string): Document title
- `content` (string): Document content (can contain quoted text with commas)

**Example:**
```csv
incident_id,doc_id,title,content
INC001,CONF001,Database Troubleshooting Guide,"Steps: 1. Check connection pool stats 2. Verify network latency 3. Review recent schema changes"
INC001,CONF002,Auth Service Runbook,"For connection issues, first check the database health dashboard"
```

### change_correlations.csv

Contains change records correlated with incidents.

**Columns:**
- `incident_id` (string): Reference to incident ID
- `change_id` (string): Unique change identifier
- `description` (string): Change description
- `deployed_at` (datetime): ISO 8601 timestamp with timezone (e.g., "2026-01-15T14:00:00Z")
- `correlation_score` (float): Correlation score between 0.0 and 1.0

**Example:**
```csv
incident_id,change_id,description,deployed_at,correlation_score
INC001,CHG001,Database schema update,2026-01-15T14:00:00Z,0.85
INC001,CHG002,Auth service config update,2026-01-16T09:00:00Z,0.72
```

## Editing CSV Files

### Using Spreadsheet Applications

1. Open the CSV file in Excel, Google Sheets, or LibreOffice Calc
2. Edit data as needed
3. Save as CSV (ensure UTF-8 encoding if available)

### Using Text Editors

1. Open the CSV file in any text editor
2. Ensure commas separate fields
3. Use quotes around fields containing commas or newlines
4. Save with UTF-8 encoding

### Best Practices

- **Headers**: First row must contain column headers (do not modify)
- **Required fields**: All columns must have values except where noted as optional
- **Empty values**: Use empty string (nothing between commas) for optional fields
- **Dates**: Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SSZ)
- **Lists**: Use pipe character (|) to separate list items in affected_services
- **Quotes**: Wrap fields in double quotes if they contain commas or special characters
- **Encoding**: Always use UTF-8 encoding when saving CSV files

## Error Handling

If CSV files are missing or malformed at startup:
- A warning is printed to stderr
- Empty data structures are used to prevent application crash
- Check application logs for specific error messages

Common errors:
- **Missing file**: Ensure all four CSV files exist in the `csv/` directory
- **Missing columns**: Verify CSV headers match the expected format
- **Invalid datetime**: Use ISO 8601 format (e.g., "2026-01-17T10:30:00")
- **Invalid correlation score**: Must be a number between 0.0 and 1.0
- **Encoding issues**: Save files with UTF-8 encoding

## Reloading Data

To reload mock data without restarting the server:

```python
from backend.data.mock_data import reload_mock_data

# Reload all CSV files
reload_mock_data()
```

This utility function re-reads all CSV files and updates the in-memory data structures.

## Testing

Run the mock data test suite to verify CSV files are correctly formatted:

```bash
cd backend
pytest tests/test_mock_data.py -v
```

The test suite includes:
- Data loading validation
- Structure verification
- Error handling tests
- Backward compatibility checks

## Adding New Test Scenarios

To add new test scenarios:

1. Add new rows to the appropriate CSV file(s)
2. Ensure incident IDs are unique in `incidents.csv`
3. Link related data using matching `incident_id` values
4. Run tests to verify the data loads correctly
5. Commit CSV changes to version control

## Example: Adding a New Incident

1. Add incident to `incidents.csv`:
```csv
INC003,Email delivery failure,Users unable to receive password reset emails,critical,open,2026-01-18T09:00:00,email-service,support-team
```

2. Add related tickets to `servicenow_tickets.csv`:
```csv
INC003,SNOW005,similar_incident,Restarted email service workers and cleared queue,,servicenow
```

3. Add documentation to `confluence_docs.csv`:
```csv
INC003,CONF004,Email Service Troubleshooting,"Check SMTP logs and verify email queue health"
```

4. Add changes to `change_correlations.csv`:
```csv
INC003,CHG004,Email service config update,2026-01-18T08:00:00Z,0.95
```

5. Test your changes:
```bash
pytest tests/test_mock_data.py -v
```
