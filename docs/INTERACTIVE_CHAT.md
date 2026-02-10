# Interactive Chat with Streaming Implementation

## Overview

This document describes the implementation of interactive chat functionality with Server-Sent Events (SSE) streaming and agent result caching for SmartRecover.

## Recent Updates

**2026-02-10**: Fixed issue where logs and events context was not being included in chat responses. All agent data (ServiceNow, Knowledge Base, Changes, Logs, and Events) is now properly included in the chat context.

## Features

### 1. Interactive Chat
- Users can have multi-turn conversations about incidents
- Questions are passed directly to the LLM with full context
- Conversation history is maintained across messages

### 2. Streaming Responses
- Real-time streaming of LLM responses using Server-Sent Events (SSE)
- Visual indicator shows when content is being streamed
- Graceful error handling for connection issues

### 3. Agent Result Caching
- In-memory cache with configurable TTL (default: 5 minutes)
- Prevents re-running expensive agent queries for the same incident
- Thread-safe implementation with automatic expiry
- First request runs all agents, subsequent requests use cached data

### 4. Complete Agent Context
- Chat responses include data from **all 5 agents**:
  1. **ServiceNow Agent**: Historical incidents and resolutions
  2. **Knowledge Base Agent**: Relevant documentation and runbooks
  3. **Change Correlation Agent**: Recent changes that may have caused the incident
  4. **Logs Agent**: Relevant log entries from Splunk with confidence scores
  5. **Events Agent**: Real-time application events from AppDynamics with confidence scores
- Each log and event includes a confidence score indicating relevance
- Top 5 most relevant logs and events are included in context

## Testing

### Backend Tests

**Cache Tests** (`tests/test_cache.py`): 9 tests passing
**Streaming Tests** (`tests/test_chat_streaming.py`): 5 tests passing

**Run Tests:**
```bash
cd backend
pytest tests/test_cache.py -v
pytest tests/test_chat_streaming.py -v
```

## Usage

When an LLM provider is configured, users can:
1. Select an incident from the sidebar
2. Ask questions about the incident
3. See responses stream in real-time
4. Continue conversations with context maintained
5. Benefit from cached agent data on follow-up questions
6. Get insights from logs and events automatically included in responses

## Context Included in Responses

The chat system provides comprehensive context from all agents:

### Change Correlation
- Top suspect change with correlation score
- Recent high-correlation changes

### Historical Data
- Similar incidents from the past
- Previous resolutions that worked

### Documentation
- Relevant knowledge base articles
- Runbook content and procedures

### Diagnostic Data (New)
- **Log Entries**: Error and warning logs with confidence scores
- **Application Events**: Performance metrics and alerts with confidence scores

### Example Context
```
TOP SUSPECT CHANGE:
- Change ID: CHG123
- Description: Updated authentication service
- Deployed At: 2024-01-15T10:30:00
- Correlation Score: 95%

SIMILAR HISTORICAL INCIDENTS: 3 found
1. Auth service timeout (resolved)
2. Login failures after deployment

RELEVANT LOG ENTRIES: 15 found
Errors: 5, Warnings: 7
1. [ERROR] auth-service: Connection pool exhausted (confidence: 85%)
2. [WARN] api-gateway: High response latency (confidence: 70%)

RELEVANT EVENTS: 12 found
Critical: 3, Warnings: 6
1. [CRITICAL] Auth-Service: Response time exceeded 5000ms (confidence: 90%)
2. [WARNING] Database: CPU utilization at 85% (confidence: 75%)
```

## Related Documentation
- [CHAT_CONTEXT_FIX.md](CHAT_CONTEXT_FIX.md) - Details on the logs and events context enhancement
