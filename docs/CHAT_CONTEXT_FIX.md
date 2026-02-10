# Chat Context Enhancement

## Overview
This document describes the fix implemented to ensure all agent context is available in the chat session.

## Problem
The interactive chat functionality was not including complete context from all agents. Specifically:
- **LogsAgent** results (Splunk log entries) were being collected but not passed to the LLM
- **EventsAgent** results (AppDynamics events) were being collected but not passed to the LLM

This meant users asking questions in the chat were missing critical diagnostic information from logs and real-time application events.

## Root Cause
In `backend/agents/orchestrator.py`, the `_build_context_from_agent_data()` method only accepted 4 parameters:
1. `incident_id`
2. `servicenow` (historical incidents)
3. `confluence` (knowledge base docs)
4. `changes` (change correlations)

However, the orchestrator was collecting data from **5 agents**:
1. ServiceNowAgent
2. KnowledgeBaseAgent
3. ChangeCorrelationAgent
4. **LogsAgent** ← Missing from context
5. **EventsAgent** ← Missing from context

## Solution
Updated the `_build_context_from_agent_data()` method to:
1. Accept two additional parameters: `logs` and `events`
2. Format and include log entries in the context
3. Format and include application events in the context

### Changes Made

#### File: `backend/agents/orchestrator.py`

**Method Signature Update:**
```python
def _build_context_from_agent_data(
    self,
    incident_id: str,
    servicenow: Dict,
    confluence: Dict,
    changes: Dict,
    logs: Dict,        # NEW
    events: Dict       # NEW
) -> str:
```

**Context Building for Logs:**
```python
if logs.get("logs"):
    context_parts.append(f"\nRELEVANT LOG ENTRIES: {logs.get('total_count', 0)} found")
    context_parts.append(f"Errors: {logs.get('error_count', 0)}, Warnings: {logs.get('warning_count', 0)}")
    for i, log in enumerate(logs['logs'][:5], 1):
        context_parts.append(
            f"{i}. [{log.get('level', 'N/A')}] {log.get('service', 'N/A')}: {log.get('message', 'N/A')} "
            f"(confidence: {log.get('confidence_score', 0):.0%})"
        )
```

**Context Building for Events:**
```python
if events.get("events"):
    context_parts.append(f"\nRELEVANT EVENTS: {events.get('total_count', 0)} found")
    context_parts.append(f"Critical: {events.get('critical_count', 0)}, Warnings: {events.get('warning_count', 0)}")
    for i, event in enumerate(events['events'][:5], 1):
        context_parts.append(
            f"{i}. [{event.get('severity', 'N/A')}] {event.get('application', 'N/A')}: {event.get('type', 'N/A')} - {event.get('message', 'N/A')} "
            f"(confidence: {event.get('confidence_score', 0):.0%})"
        )
```

**Method Call Update:**
```python
context = self._build_context_from_agent_data(
    incident_id,
    agent_data.get("servicenow_results", {}),
    agent_data.get("confluence_results", {}),
    agent_data.get("change_results", {}),
    agent_data.get("logs_results", {}),      # NEW
    agent_data.get("events_results", {})     # NEW
)
```

## Impact

### Before Fix
Chat context included only 3 agent data sources:
```
TOP SUSPECT CHANGE: ...
SIMILAR HISTORICAL INCIDENTS: ...
PREVIOUS RESOLUTIONS: ...
RELEVANT KNOWLEDGE BASE ARTICLES: ...
```

### After Fix
Chat context now includes all 5 agent data sources:
```
TOP SUSPECT CHANGE: ...
SIMILAR HISTORICAL INCIDENTS: ...
PREVIOUS RESOLUTIONS: ...
RELEVANT KNOWLEDGE BASE ARTICLES: ...
RELEVANT LOG ENTRIES: 15 found          ← NEW
Errors: 5, Warnings: 7                  ← NEW
1. [ERROR] api-gateway: Connection timeout (confidence: 85%)
2. [WARN] database: High memory usage (confidence: 70%)
...

RELEVANT EVENTS: 12 found                ← NEW
Critical: 3, Warnings: 6                 ← NEW
1. [CRITICAL] Web-App: Slow Transaction - Response time exceeded 5000ms (confidence: 90%)
2. [WARNING] Payment-Gateway: CPU Spike - CPU at 85% (confidence: 75%)
...
```

## Benefits

1. **Complete Context**: Users now have access to all diagnostic information when asking questions
2. **Better Troubleshooting**: Log entries help identify technical issues and error patterns
3. **Real-time Insights**: Application events provide performance metrics and alerts
4. **Confidence Scores**: Each log/event shows its relevance confidence score for transparency
5. **Formatted Output**: Clean, readable format with severity levels and service names

## Testing

### Automated Tests
All existing chat streaming tests pass:
- ✅ `test_chat_stream_with_mock_llm`
- ✅ `test_chat_stream_uses_cache`
- ✅ `test_chat_stream_with_conversation_history`
- ✅ `test_chat_stream_context_includes_agent_data`
- ✅ `test_chat_stream_error_handling`

### Manual Verification
Created test script demonstrating:
- Logs are properly formatted with level, service, message, and confidence
- Events are properly formatted with severity, application, type, message, and confidence
- Context includes summary statistics (total count, error count, etc.)
- Top 5 most relevant items are shown for both logs and events

## Example Usage

When a user asks a question about an incident:

**User:** "What errors are showing in the logs?"

**Previous Response (Missing Context):**
> I don't have specific log information available for this incident.

**New Response (With Context):**
> Based on the log entries, I can see 5 errors including:
> 1. Connection timeout in the api-gateway (85% confidence)
> 2. Database connection pool exhausted
> 3. Circuit breaker opened for external API
> 
> The most relevant error appears to be the api-gateway timeout, which correlates with the reported incident.

## Related Files
- `backend/agents/orchestrator.py` - Main implementation
- `backend/agents/logs_agent.py` - Provides log data structure
- `backend/agents/events_agent.py` - Provides event data structure
- `backend/tests/test_chat_streaming.py` - Test coverage

## Future Enhancements
1. Add support for filtering logs/events by time window
2. Implement log pattern detection and highlighting
3. Add drill-down capability for specific log/event details
4. Include log/event trends over time
5. Add correlation between logs and events

## Backward Compatibility
✅ **Fully backward compatible** - No breaking changes to:
- API endpoints
- Data models
- Agent interfaces
- Existing tests
