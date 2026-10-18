# Implementation Summary: SmartRecover Admin Panel & Mock Data Expansion

## Overview
This implementation adds two major features to SmartRecover:
1. **10x Mock Data Expansion**: Scaled test data from 150 to 1500 incidents
2. **Agent Prompts Management**: New admin panel section for managing AI agent prompts

## Automation Rules and Gate Behavior

- Category-based auto-remediation rules are stored in `backend/data/automation_rules.json`.
- Automation audit history is stored separately in `backend/data/automation_audit.json`.
- The automation gate runs after synthesis and is deny-by-default: it requires the global kill switch to be enabled, a known incident category, an enabled category rule, a suggested fix, sufficient overall confidence, sufficient suggested-fix confidence, and risk/severity values within the configured limits.
- Missing or corrupt rules/audit files fall back safely to defaults instead of failing requests.

## Live Incident Ingestion

The incident API and orchestrator use the same configured source. The default
`incident_management.connector_type` in `backend/config.yaml` is `mock`.
Set it to `servicenow` or `jira`, or override it with `CONNECTOR_TYPE`.
Restart the backend after changing source configuration.

| Source | Non-secret settings (environment variable overrides YAML) | Required secret (environment only) |
|--------|----------------------------------------------------------|------------------------------------|
| ServiceNow | `servicenow.instance_url` / `SERVICENOW_INSTANCE_URL`, `servicenow.username` / `SERVICENOW_USERNAME` | `SERVICENOW_PASSWORD` |
| Jira Cloud | `jira.url` / `JIRA_URL`, `jira.username` / `JIRA_USERNAME`, `jira.project_key` / `JIRA_PROJECT_KEY` | `JIRA_API_TOKEN` |

The YAML source settings live under `incident_management`. URLs must use HTTPS,
without embedded credentials, query parameters, or fragments. Use a read-only
integration account. ServiceNow uses basic authentication; OAuth client credentials
are not supported by this read path. Jira Cloud uses an account email and API token;
Jira Server/Data Center is not supported. Secrets in YAML are ignored.

### Read contract

- ServiceNow reads the incident table with the Table API, using incident numbers
  (`INC` followed by digits) as public IDs. It requests raw values and display
  labels and paginates by offset.
- Jira reads all visible issues in the configured project with
  `GET /rest/api/3/search/jql`, using enhanced-search continuation tokens. Issue
  keys are preserved and lookups cannot escape the configured project.
- Both readers follow all pages, with 100 records requested per page and a
  1,000-page safety limit. Repeated pages or reaching the limit fail explicitly,
  rather than returning a misleading partial catalog. HTTP requests time out
  after 30 seconds; authentication, rate-limit, network, malformed-response, and
  pagination failures are reported, not replaced with mock data. API reads return
  a sanitized `502`; missing incident IDs return `404`.
- Dates are normalized to UTC. Common upstream priority/status values map to
  SmartRecover severity/status. Unknown priorities become `unknown` so automation
  fails closed; unknown states are logged and shown as investigating.
- Similar incidents use the existing local similarity algorithm over resolved
  upstream records. ServiceNow close notes provide prior resolutions; Jira's
  generic resolution label is not treated as an actionable remediation procedure.

### Category mapping

Metadata matching is case-insensitive, trims whitespace, and normalizes spaces,
hyphens, and underscores. Canonical names are accepted directly.

| Source | Precedence |
|--------|------------|
| ServiceNow | Recognized raw `subcategory`, then raw `category`, then existing title/description inference |
| Jira | Components agreeing on one recognized category, then recognized issue type, then existing title/description inference |

Conflicting Jira components never depend on their order: they fall through to
issue type/text and produce a warning. Unmapped metadata also produces a warning.
Fallback retains the existing `Application` default when no text keywords match.

Supported aliases: `software`/`email` -> Application; `hardware`/`server`/
`operating system` -> Infrastructure; `db`/`sql` -> Database; `authentication`/
`certificate` -> Security; `disk` -> Storage; `logging` -> Monitoring;
`redis`/`cdn` -> Cache; `payment` -> Payments. Mapping is exact, not fuzzy;
custom labels such as `payments-team` are not automatically trusted.

### Read-only boundaries

Incident list/detail/context, resolution analysis (including SSE), chat,
exclusions, and incident-based MTTR/trend calculations use the live source.
The same fetched incident category reaches graph and streaming automation
evaluation and audit records. Upstream incidents are not copied into mock CSVs.

Status updates, resolution submissions, and resolution-draft requests return
`405` in live mode with an explicit read-only message. The existing UI reports
these API errors; perform those actions in ServiceNow/Jira. Analysis and local
feedback/audit records are still supported.

Live change ingestion, logs, events, and remediation scripts are not implemented.
Their mock-only agents explicitly report unavailable data in live mode; mock KB
and mock metrics are likewise excluded rather than mixing demo evidence into a
real incident. Configure non-mock KB/metrics sources separately when needed.
Automation remains simulated, and without a real suggested fix it remains blocked.
Switching source should use a separate deployment/data directory for local
feedback/audit history: those existing stores are keyed by incident ID, not tenant.

Tests use `httpx.MockTransport` fixtures rather than real accounts:
`python -m pytest backend/tests/test_live_incident_connectors.py backend/tests/test_categorization.py`.

## Feature 1: Mock Data Expansion (10x Scale)

### Changes Made
- **Data Generation**: Used `generate_mock_data.py --incidents 1500` to create 10x data
- **Results**:
  - 1500 incidents (previously 150)
  - 2956 tickets (previously 293)
  - 2260 documentation entries (previously 232)
  - 2254 change correlations (previously 233)
- **Validation**: All data passed validation with unique IDs
- **Lazy Loading**: Tested and verified (loads 10 sample incidents in lazy mode)

### Usage
```bash
# Generate 10x data (1500 incidents)
cd backend/data
python generate_mock_data.py --incidents 1500 --validate

# Generate with scaling factor
python generate_mock_data.py --scale 10 --validate

# Preserve existing data and add more
python generate_mock_data.py --scale 15 --validate --preserve-existing

# Enable lazy loading (loads only 10 incidents at startup)
export SMARTRECOVER_LAZY_LOADING=true
```

### Data Quality
- All incident IDs are unique (INC001-INC1500)
- All ticket IDs are unique (SNOW001-SNOW1500, JIRA-001-JIRA-1456)
- Relationships between incidents, tickets, docs, and changes are preserved
- Realistic data patterns maintained across all generated records

## Feature 2: Agent Prompts Management

### Backend Implementation

#### New File: `backend/prompts.py`
- **PromptManager Class**: Manages agent prompts with JSON persistence
- **Default Prompts**: Defined for 4 agents:
  - `orchestrator`: Main incident resolution coordinator
  - `servicenow`: Historical incident analysis
  - `knowledge_base`: Documentation retrieval
  - `change_correlation`: Change correlation analysis
- **Storage**: Custom prompts saved to `backend/data/custom_prompts.json`

#### New API Endpoints
1. **GET `/api/v1/admin/agent-prompts`**
   - Returns all agent prompts with current, default, and is_custom flags
   - Response: `AgentPromptsResponse` with prompt info for each agent

2. **PUT `/api/v1/admin/agent-prompts/{agent_name}`**
   - Updates prompt for specific agent
   - Request body: `{ "prompt": "new prompt text" }`
   - Response: Updated `AgentPromptInfo`

3. **POST `/api/v1/admin/agent-prompts/reset`**
   - Resets prompts to defaults
   - Query param `agent_name` (optional): Reset specific agent or all
   - Response: `{ "message": "..." }`

### Frontend Implementation

#### Updated: `frontend/src/components/Admin.tsx`
- Added "Agent Prompts Management" section
- Features:
  - Agent selector dropdown (shows ✏️ icon for custom prompts)
  - Large text area for editing prompts
  - Status badge (Custom/Default)
  - Action buttons:
    - **Save Prompt**: Save changes for current agent
    - **Reset to Default**: Reset current agent's prompt
    - **Reset All Prompts**: Reset all agents to defaults
  - Default prompt display for comparison
  - Success/error message handling

#### Updated: `frontend/src/services/api.ts`
- Added 3 new API methods:
  - `getAgentPrompts()`: Fetch all prompts
  - `updateAgentPrompt(agentName, prompt)`: Update a prompt
  - `resetAgentPrompts(agentName?)`: Reset one or all prompts

#### Updated: `frontend/src/types/incident.ts`
- Added TypeScript types:
  - `AgentPromptInfo`: Prompt metadata
  - `AgentPromptsResponse`: API response structure
  - `UpdateAgentPromptRequest`: Update request structure

#### Updated: `frontend/src/components/Admin.css`
- Added comprehensive styling for:
  - Agent selector dropdown
  - Prompt textarea (monospace font, 12 rows)
  - Action buttons (Save, Reset, Reset All)
  - Status badges (Custom/Default)
  - Default prompt display section
  - Responsive layout with proper spacing

### Admin Panel Organization

The Admin panel now has three clear sections:

1. **Logging Configuration**
   - Log level selection
   - Tracing enable/disable
   - Real-time configuration updates

2. **Current LLM Configuration**
   - Provider information
   - Model details
   - Connection status

3. **Test LLM Connection**
   - Send test messages
   - View responses
   - Validate LLM communication

4. **Agent Prompts Management** (NEW)
   - Select agent
   - Edit prompts
   - Compare with defaults
   - Reset functionality

## Testing

### Backend Tests
```bash
# Test prompt manager
cd backend
python << 'EOF'
from prompts import get_prompt_manager
pm = get_prompt_manager()
print(pm.get_all_prompts())
EOF

# Test data generation
cd backend/data
python generate_mock_data.py --incidents 100 --validate

# Test lazy loading
SMARTRECOVER_LAZY_LOADING=true python -c "from data import mock_data; print(f'Loaded {len(mock_data.MOCK_INCIDENTS)} incidents')"
```

### Frontend Tests
```bash
# Run frontend tests
cd frontend
npm test
```

### Integration Tests
```bash
# Start full stack
./start.sh

# Navigate to http://localhost:3000/admin
# Test Agent Prompts section:
# 1. Select different agents
# 2. Modify a prompt and save
# 3. Verify custom badge appears
# 4. Reset prompt and verify it reverts
# 5. Test Reset All Prompts
```

## Configuration

### Environment Variables
- `SMARTRECOVER_LAZY_LOADING`: Enable lazy loading (default: false)
- `SMARTRECOVER_BATCH_SIZE`: Batch size for lazy loading (default: 50)

### Files
- `backend/data/csv/`: Contains all CSV data files
- `backend/data/custom_prompts.json`: Stores custom agent prompts
- `backend/prompts.py`: Prompt management logic

## API Documentation

### Agent Prompts Endpoints

#### Get All Agent Prompts
```
GET /api/v1/admin/agent-prompts
Response: {
  "prompts": {
    "orchestrator": {
      "current": "...",
      "default": "...",
      "is_custom": false
    },
    ...
  }
}
```

#### Update Agent Prompt
```
PUT /api/v1/admin/agent-prompts/{agent_name}
Request: { "prompt": "new prompt text" }
Response: {
  "current": "new prompt text",
  "default": "...",
  "is_custom": true
}
```

#### Reset Agent Prompts
```
POST /api/v1/admin/agent-prompts/reset?agent_name=orchestrator
Response: { "message": "Prompt reset successfully for orchestrator" }

POST /api/v1/admin/agent-prompts/reset
Response: { "message": "All prompts reset successfully" }
```

## Benefits

### Mock Data Expansion
- **Realistic Testing**: 10x more data for testing pagination, search, and performance
- **Scalability Testing**: Validate system behavior with larger datasets
- **Lazy Loading**: Efficient memory usage for large datasets
- **Data Quality**: Maintained relationships and realistic patterns

### Agent Prompts Management
- **Customization**: Easily tune agent behavior without code changes
- **Experimentation**: Test different prompts for better results
- **Reset Safety**: Always able to revert to defaults
- **Visibility**: Compare custom prompts with defaults
- **Persistence**: Custom prompts survive server restarts

## Future Enhancements

1. **Prompt Versioning**: Track prompt changes over time
2. **Prompt Templates**: Provide multiple preset prompts
3. **A/B Testing**: Compare different prompts side-by-side
4. **Prompt Validation**: Validate prompt structure before saving
5. **Import/Export**: Share prompts between environments
6. **Agent Performance Metrics**: Track how different prompts affect outcomes

## Files Modified

### Backend
- `backend/api/routes.py`: Added 3 new endpoints for agent prompts
- `backend/prompts.py`: NEW - Prompt management system
- `backend/data/csv/*.csv`: Updated with 10x data

### Frontend
- `frontend/src/components/Admin.tsx`: Added Agent Prompts section
- `frontend/src/components/Admin.css`: Added prompt editor styling
- `frontend/src/services/api.ts`: Added prompt API methods
- `frontend/src/types/incident.ts`: Added prompt types

## Verification

All features have been implemented and tested:
- ✅ Mock data expanded to 1500 incidents with validation
- ✅ Lazy loading tested and working
- ✅ Unique ticket IDs verified
- ✅ Prompt manager backend implemented
- ✅ API endpoints created and tested
- ✅ Frontend UI implemented
- ✅ TypeScript types defined
- ✅ CSS styling applied
- ✅ Basic functionality tests passed
