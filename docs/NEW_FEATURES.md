# SmartRecover - New Features Guide

## 🎉 What's New

### 1. Mock Data Expansion (10x Scale)
The test/mock data has been expanded by a factor of 10 to support more realistic testing and development scenarios.

**Before:** 150 incidents, ~290 tickets, ~230 docs, ~230 changes  
**After:** 1500 incidents, 2956 tickets, 2260 docs, 2254 changes

### 2. Agent Prompts Management
A new admin panel section allows you to customize and manage the AI prompts used by different agents in the incident resolution workflow.

## 📊 Mock Data Features

### Data Scale
- **1500 incidents** with realistic titles, descriptions, and metadata
- **2956 tickets** with unique IDs and relationships
- **2260 documentation entries** with relevant content
- **2254 change correlations** with temporal relationships

### Data Quality
- ✅ All IDs are unique and validated
- ✅ Relationships between incidents, tickets, docs, and changes are preserved
- ✅ Realistic data patterns across severity, status, and services
- ✅ Temporal coherence (changes before incidents, resolutions after)

### Lazy Loading Support
For large datasets, enable lazy loading to reduce memory usage:

```bash
# Enable lazy loading (loads only 10 incidents at startup)
export SMARTRECOVER_LAZY_LOADING=true
export SMARTRECOVER_BATCH_SIZE=50  # Optional: set batch size

# Start the application
./start.sh
```

### Generating Custom Data

Generate data with specific requirements:

```bash
cd backend/data

# Generate exact number of incidents
python generate_mock_data.py --incidents 2000 --validate

# Use scaling factor (multiplies base of 15 incidents)
python generate_mock_data.py --scale 20 --validate

# Preserve existing data and add more
python generate_mock_data.py --scale 15 --preserve-existing --validate

# Use custom seed for reproducibility
python generate_mock_data.py --incidents 1000 --seed 123 --validate
```

## 🤖 Agent Prompts Management

### Overview
The Agent Prompts Management feature allows you to customize the system prompts used by different AI agents in the incident resolution workflow. This enables you to:
- Fine-tune agent behavior without code changes
- Experiment with different prompting strategies
- Optimize responses for your specific use case
- Reset to defaults at any time

### Accessing the Feature

1. Start SmartRecover: `./start.sh`
2. Navigate to the Admin panel: http://localhost:3000/admin
3. Scroll to the "Agent Prompts Management" section

### Available Agents

SmartRecover uses 4 specialized agents:

1. **Orchestrator** - Main coordinator that synthesizes information from all agents
2. **ServiceNow** - Finds similar historical incidents and resolutions
3. **Knowledge Base** - Retrieves relevant documentation and runbooks
4. **Change Correlation** - Identifies recent changes that may have caused incidents

### Using the Interface

#### View Prompts
- Select an agent from the dropdown
- Current prompt is displayed in the text area
- Default prompt is shown below for comparison
- Custom prompts show a ✏️ icon in the dropdown

#### Edit Prompts
1. Select an agent
2. Modify the prompt text in the text area
3. Click "Save Prompt"
4. Success message confirms the save

#### Reset Prompts
- **Reset to Default**: Resets the current agent's prompt
- **Reset All Prompts**: Resets all agents to their defaults
- Requires confirmation before resetting

### Prompt Tips

**Good Prompts:**
- Clear and specific about the agent's role
- Include expected output format
- Mention key considerations
- Keep consistent tone across agents

**Example Prompt Structure:**
```
You are an expert [ROLE].
Your task is to [MAIN OBJECTIVE].

Focus on:
- [KEY POINT 1]
- [KEY POINT 2]
- [KEY POINT 3]

Return [OUTPUT FORMAT].
```

## 📖 API Documentation

### Agent Prompts Endpoints

#### Get All Agent Prompts
```http
GET /api/v1/admin/agent-prompts
```

**Response:**
```json
{
  "prompts": {
    "orchestrator": {
      "current": "You are an expert incident resolution assistant...",
      "default": "You are an expert incident resolution assistant...",
      "is_custom": false
    },
    "servicenow": { ... },
    "knowledge_base": { ... },
    "change_correlation": { ... }
  }
}
```

#### Update Agent Prompt
```http
PUT /api/v1/admin/agent-prompts/{agent_name}
Content-Type: application/json

{
  "prompt": "Your custom prompt here..."
}
```

**Response:**
```json
{
  "current": "Your custom prompt here...",
  "default": "Original default prompt...",
  "is_custom": true
}
```

#### Reset Agent Prompts
```http
# Reset specific agent
POST /api/v1/admin/agent-prompts/reset?agent_name=orchestrator

# Reset all agents
POST /api/v1/admin/agent-prompts/reset
```

**Response:**
```json
{
  "message": "Prompt reset successfully for orchestrator"
}
```

## 🔧 Configuration

### Environment Variables
- `SMARTRECOVER_LAZY_LOADING`: Enable lazy loading (default: `false`)
- `SMARTRECOVER_BATCH_SIZE`: Batch size for lazy loading (default: `50`)

### Files
- `backend/data/csv/`: CSV data files (incidents, tickets, docs, changes)
- `backend/data/custom_prompts.json`: Custom agent prompts storage
- `backend/prompts.py`: Prompt management logic

### Persistence
Custom prompts are automatically saved to `backend/data/custom_prompts.json` and persist across server restarts.

## 🧪 Testing

### Test Mock Data
```bash
# Test data generation
cd backend/data
python generate_mock_data.py --incidents 100 --validate

# Test lazy loading
cd backend
SMARTRECOVER_LAZY_LOADING=true python -c "from data import mock_data; print(f'Loaded {len(mock_data.MOCK_INCIDENTS)} incidents')"
```

### Test Prompt Management
```bash
cd backend
python << 'EOF'
from prompts import get_prompt_manager
pm = get_prompt_manager()

# Get all prompts
prompts = pm.get_all_prompts()
print(f"Agents: {list(prompts.keys())}")

# Set custom prompt
pm.set_prompt('orchestrator', 'Custom prompt')
print(f"Is custom: {pm.get_all_prompts()['orchestrator']['is_custom']}")

# Reset
pm.reset_prompt('orchestrator')
print("Reset complete")
EOF
```

### Test Admin Panel
1. Start the application: `./start.sh`
2. Navigate to http://localhost:3000/admin
3. Test each section:
   - Logging configuration
   - LLM testing
   - Agent prompts management

## 📚 Documentation

For detailed implementation notes, see:
- [IMPLEMENTATION_NOTES.md](./IMPLEMENTATION_NOTES.md) - Complete technical details
- [README.md](../README.md) - Main project documentation

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/jmgress/SmartRecover.git
cd SmartRecover

# 2. Start the application
./start.sh

# 3. Access the admin panel
# Navigate to: http://localhost:3000/admin

# 4. Customize agent prompts
# - Select an agent
# - Edit the prompt
# - Save changes
```

## 🤝 Contributing

When modifying prompts or data:
1. Test thoroughly with representative incidents
2. Document any significant prompt changes
3. Validate data generation with `--validate` flag
4. Ensure backward compatibility

## 📞 Support

For issues or questions:
- Check the documentation in `docs/`
- Review the implementation notes
- Examine the example prompts in `backend/prompts.py`
