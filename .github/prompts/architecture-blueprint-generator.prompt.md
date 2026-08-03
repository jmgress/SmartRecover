---
mode: agent
description: 'Analyze the codebase and generate a comprehensive project architecture blueprint document.'
---

# Project Architecture Blueprint Generator

Analyze this codebase and produce a `Project_Architecture_Blueprint.md` that serves as a definitive reference for maintaining architectural consistency. Ground everything in the **actual** implementation you find — do not describe theoretical patterns the code doesn't use.

## Inputs
- **Detail level**: ${input:DETAIL_LEVEL:high-level, detailed, or comprehensive (default: detailed)}
- **Diagram style**: ${input:DIAGRAM_STYLE:mermaid, C4, or none (default: mermaid)}
- **Focus area**: ${input:FOCUS:leave blank for the whole repo, or name an area e.g. backend agents, connectors, frontend}

## Steps

### 1. Detect the architecture
- Identify the technology stacks and frameworks by inspecting `backend/requirements.txt`, `frontend/package.json`, config files, and import statements.
- Determine the architectural patterns from folder organization, dependency flow, and component boundaries (e.g. the LangGraph orchestrator + pluggable-connector design).

### 2. Overview
- Explain the overall architectural approach and guiding principles evident in the code.
- Identify architectural boundaries and how they're enforced (abstract base classes, factory methods, config models).

### 3. Visualization
- If a diagram style other than `none` was requested, include diagrams at multiple abstraction levels: a high-level subsystem view, a component-interaction view, and a data-flow view. Use ```mermaid fenced blocks for Mermaid. Diagrams must reflect the real implementation.

### 4. Core components
For each major component (e.g. `OrchestratorAgent`, the specialized agents, connectors, API layer, config, logging), document: purpose/responsibility, internal structure, interaction patterns, and extension points.

### 5. Layers & dependencies
Map the layer structure as implemented, document dependency directions, and note any circular dependencies or boundary violations.

### 6. Data architecture
Document the domain models (`backend/models/incident.py`), the mock-data sources (`backend/data/`), connector result shapes, and any caching (`backend/cache/`).

### 7. Cross-cutting concerns
Document how the codebase handles: configuration (env vars > `config.yaml` > defaults), logging/tracing (`get_logger`, `@trace_async_execution`), error handling, input validation (Pydantic at API boundaries), and secret management (env-var-only credentials).

### 8. Communication patterns
Document the FastAPI `/api/v1` surface, request/response contracts, streaming endpoints, and the sequential LangGraph agent flow.

### 9. Testing architecture
Document the pytest + asyncio strategy, mock-first approach, and shared fixtures in `backend/tests/conftest.py`, plus the frontend Jest/RTL setup.

### 10. Blueprint for new development
Provide concrete guidance for adding new agents, connectors, and API routes (where files go, which base classes/factories to use, how to wire the orchestrator), and list common pitfalls to avoid.

Note the generation date and recommend keeping the blueprint updated as the architecture evolves.
