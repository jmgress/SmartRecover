---
mode: agent
description: 'Scaffold a new SmartRecover backend agent and wire it into the LangGraph orchestrator with a test.'
---

# Add a New Agent

Create a new backend agent named **${input:AGENT_NAME:e.g. metrics_agent}** whose job is: ${input:PURPOSE:describe what this agent should retrieve or compute}.

Ground every step in the existing code — read a current agent (e.g. `backend/agents/remediation_agent.py`) and `backend/agents/orchestrator.py` before writing.

## Steps
1. **Create the agent** at `backend/agents/${input:AGENT_NAME}.py`:
   - Implement `async def query(self, incident_id: str, context: str) -> Dict[str, Any]`.
   - Decorate it with `@trace_async_execution` from `backend.utils.logger` and get a logger via `get_logger(__name__)`.
   - Return a dict that includes a `source` key identifying the agent.
   - If it reads from an external system, add a `from_config(cls, config)` factory and default to a mock connector.
2. **Wire it into the orchestrator** in `backend/agents/orchestrator.py`:
   - Add a result key to the `IncidentState` TypedDict.
   - Instantiate the agent in `OrchestratorAgent.__init__`.
   - Add a node in `_build_graph()` and connect it with `workflow.add_edge()` in the existing sequential flow.
   - Fold its output into `_synthesize_results` / `final_response`.
3. **Add a test** at `backend/tests/test_${input:AGENT_NAME}.py`:
   - Use `@pytest.mark.asyncio`, call `await agent.query("INC001", "")`, and assert on the `source` key and expected result structure.
   - Stay mock-first; reuse fixtures from `backend/tests/conftest.py`.
4. **Verify**: run `cd backend && python -m pytest tests/test_${input:AGENT_NAME}.py -v`, then `./test.sh --backend`.

## Constraints
- Do not add new dependencies unless required.
- Read secrets from environment variables only; never hardcode credentials.
- Follow `backend-python.instructions.md` and `backend-tests.instructions.md`.
