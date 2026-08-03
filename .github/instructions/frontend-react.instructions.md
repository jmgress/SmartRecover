---
applyTo: 'frontend/src/**/*.{ts,tsx}'
description: 'Coding rules for the SmartRecover React 19 + TypeScript frontend.'
---

# Frontend React Rules

- Stack is React 19 with TypeScript (strict types). Build/test tooling is CRACO (`craco start|build|test`).
- Route all backend calls through the `api` client in `frontend/src/services/api.ts` (base URL `process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1'`). Do not scatter raw `fetch()` calls or hardcode the API host in components.
- Add shared TypeScript types under `frontend/src/types/` and reuse them for request/response shapes instead of `any`.
- Keep components in `frontend/src/components/`, reusable logic in `frontend/src/hooks/`, and helpers in `frontend/src/utils/`.
- Tests use Jest + React Testing Library (`@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`), configured in `frontend/src/setupTests.ts`. Prefer user-facing, role-based queries (`getByRole`, `getByLabelText`, `getByText`) over test IDs or implementation details.
- Run frontend tests with `./test.sh --frontend` (equivalent to `CI=true npm test -- --coverage --watchAll=false`).
- Never expose API keys or secrets in frontend code; the frontend talks only to the backend `/api/v1` surface.
