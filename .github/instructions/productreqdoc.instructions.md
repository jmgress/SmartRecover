---
description: 'Maintains a living Product Requirements Document (prd.md) that stays in sync with every feature request, bug fix, or architectural change.'
applyTo: '**'
---

# Product Requirements Document — Maintenance Instructions

## Purpose

You are responsible for keeping the project's **Product Requirements Document** (`prd.md` at the repository root) accurate and up-to-date. Every time a user asks you to implement a feature, fix a bug, change behavior, add an integration, or modify architecture, you **must** update `prd.md` to reflect the change.

## Core Rules

### 1. If `prd.md` Does Not Exist — Create It
Before making any change, check whether `prd.md` exists at the repository root. If it does not:
1. Generate a comprehensive PRD based on the **current** functionality of the project (codebase, README, docs, config, tests).
2. Follow the canonical structure defined below.
3. Create the file, then proceed with the user's request and append/update the relevant sections.

### 2. If `prd.md` Exists — Update It
For every user request that changes product behavior:
1. Read the current `prd.md`.
2. Determine which sections are affected.
3. **Add** new requirements, features, or non-functional changes to the appropriate section.
4. **Update** existing entries when behavior changes (do not leave stale descriptions).
5. **Mark items as deprecated or removed** rather than silently deleting them, unless the user explicitly asks for removal.
6. Append a dated entry to the **Change Log** section at the bottom.

### 3. Change Log Entry Format
Every update must add an entry:
```markdown
| YYYY-MM-DD | Short description of what changed | Section(s) affected |
```

### 4. Do Not Over-Document
- Keep descriptions concise and actionable.
- Avoid duplicating implementation details that belong in code comments or architecture docs.
- Focus on **what** the system should do and **why**, not **how** (unless the "how" is a hard constraint).

### 5. Versioning
- Increment the **minor** version (e.g., 1.1 → 1.2) for new features or significant changes.
- Increment the **patch** version (e.g., 1.2.1 → 1.2.2) for clarifications, small behavioral tweaks, or bug-fix documentation.
- Increment the **major** version (e.g., 1.x → 2.0) only when the user explicitly declares a major release or breaking change.

## Canonical PRD Structure

Use the following section order. Sections may be empty initially but should always be present:

```markdown
# Product Requirements Document — <Project Name>
> Version: X.Y.Z | Last updated: YYYY-MM-DD

## 1. Overview
High-level purpose and value proposition.

## 2. Goals & Success Metrics
What the product aims to achieve and how success is measured.

## 3. User Personas
Who uses the system and their key needs.

## 4. Functional Requirements
### 4.1 Core Features
### 4.2 Integrations & Data Sources
### 4.3 API Surface
### 4.4 Frontend / UI

## 5. Non-Functional Requirements
### 5.1 Performance
### 5.2 Security
### 5.3 Scalability
### 5.4 Observability & Logging
### 5.5 Testing

## 6. Architecture & Constraints
Key architectural decisions and hard constraints.

## 7. Configuration & Deployment
How the system is configured and deployed.

## 8. Out of Scope
Explicitly excluded capabilities.

## 9. Open Questions
Unresolved decisions or areas needing research.

## 10. Change Log
| Date | Change | Section(s) |
|------|--------|------------|
```

## Behavioral Guidelines

- **Be additive by default.** New requests should add to the PRD, not replace existing content, unless the user says otherwise.
- **Preserve traceability.** If a requirement evolves, keep a brief note about what it replaced in the Change Log.
- **Keep the PRD self-contained.** A reader should understand the full product scope from `prd.md` alone, without needing to read the codebase.
- **Use plain language.** Avoid jargon; the PRD should be understandable by both engineers and non-technical stakeholders.
- **Link to docs when helpful.** Reference files like `docs/IMPLEMENTATION_NOTES.md` or `README.md` for deep-dive details, but the PRD should still summarize the requirement.