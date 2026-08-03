---
description: 'Keep documentation in sync with the SmartRecover code as it changes.'
applyTo: '**/*.md'
---

# Documentation Rules

When creating or editing Markdown docs in this repo:
- Ensure documentation matches the actual code and current implementation — verify against the code before writing.
- Keep API, configuration, and workflow docs aligned with the real endpoints (`/api/v1` in `backend/api/routes.py`), config (`backend/config.py`, `backend/config.yaml`, env vars), and agent/connector behavior.
- Flag outdated, missing, or incorrect documentation and propose concrete updates.
- Keep code comments, `README.md`, and the `docs/` guides consistent with backend, frontend, and test logic.
- When a feature or behavior changes, update the relevant docs in the same change to prevent drift. (PRD updates are handled by `productreqdoc.instructions.md`.)
- Use real examples from the codebase to illustrate usage and integration points; reference existing files such as `README.md`, `IMPLEMENTATION_SUMMARY.md`, and files under `docs/`.

If documentation is unclear, incomplete, or out of sync, request clarification or propose an improvement rather than guessing.
