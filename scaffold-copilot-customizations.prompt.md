---
mode: agent
description: 'Analyze the current project and scaffold a complete, correctly-typed set of Copilot customization files (instructions, prompts, agents, skills).'
---

# Scaffold Copilot Customizations

Analyze **this** project and generate a complete set of Copilot customization files: instructions, prompts, agents, and skills. Choose the correct **type** for each item using the decision rules below, and write valid frontmatter.

## Inputs
- **Focus area** (optional): ${input:FOCUS:leave blank to cover the whole project, or name an area e.g. backend API, React UI, tests}
- **Depth**: ${input:DEPTH:balanced (or minimal, comprehensive)}

## Step 1 — Understand the project first
Before writing anything, inspect the repo to ground every file in reality:
- Detect the stack, frameworks, and folder layout (e.g. `package.json`, `requirements.txt`, `src/`, `tests/`).
- Identify the real conventions in use: how tests are written, how the API/data layer works, security-sensitive files, build/test commands.
- Note the actual test/lint/build commands so generated files reference real ones, not assumptions.
- Do **not** invent tools, CLIs, or file paths. Every reference must point to something that exists.

## Step 2 — Pick the right type for each need
Use this decision rule:

| If the need is… | Use a… | Fires when |
|-----------------|--------|------------|
| A passive coding rule/guardrail tied to certain files | **Instruction** (`.github/instructions/<name>.instructions.md`) | Automatically, when a file matching `applyTo` is in context |
| A one-shot task the user runs on demand | **Prompt** (`.github/prompts/<name>.prompt.md`) | When the user invokes `/<name>` |
| A persistent role/persona with a scoped toolset | **Agent** (`.github/agents/<name>.agent.md`) | When the user switches into the mode |
| A reusable multi-step procedure the model should invoke itself | **Skill** (`.github/skills/<name>/SKILL.md`) | Automatically, when the request matches the skill's description |

Heuristic: **rules → instruction**, **a job → prompt**, **a role → agent**, **a procedure the model discovers on its own → skill**.

Guard against the common mistakes:
- A file describing a *task* ("perform X", "review Y") is a **prompt or skill**, not an instruction.
- Broad-but-rarely-needed domain knowledge belongs in a **skill** (model-invoked), not an always-on instruction.
- Only bundle assets/reference files when the procedure genuinely needs them → that's a **skill**.

## Step 3 — Write valid frontmatter

**Instruction** — declarative rules only, scoped as narrowly as possible:
```markdown
---
applyTo: 'backend/**/*.py'
description: 'Coding rules for the <area>.'
---
```
Prefer specific globs (e.g. `**/database*.py`) over `**`. Reserve `**` for the repo-wide `.github/copilot-instructions.md` project-context file.

**Prompt** — a task; use real input syntax `${input:NAME:hint}` (never a `${VAR="a|b|c"}` DSL, and no conditional templating — VS Code cannot evaluate it):
```markdown
---
mode: agent
description: 'One-line description of the task.'
---
```

**Agent** — a role with an explicit, minimal tool list and clear boundaries:
```markdown
---
description: 'What this role does.'
tools: ['read_file', 'grep_search', 'semantic_search', 'file_search', 'list_dir']
---
```
Give read-only roles read-only tools; only add `create_file`/`replace_string_in_file`/`run_in_terminal` to roles that must edit or run code.

**Skill** — model-invoked; the description must include concrete "Use when:" triggers so the model knows when to reach for it:
```markdown
---
name: <kebab-case-name>
description: 'What it does. Use when: <trigger 1>, <trigger 2>, <trigger 3>.'
argument-hint: 'What input to pass (optional)'
---
```
Put supporting templates under `assets/` and deeper docs under `references/`, and link them from the `SKILL.md` body.

## Step 4 — Propose, then generate
1. Present a short table of the files you intend to create (path, type, one-line purpose). Aim for a coherent set, not one of everything.
2. On approval, create each file. Keep bodies concise, grounded in the real codebase, and free of invented commands.
3. For each item, briefly justify **why that type** — this doubles as a teaching artifact.

## Quality bar
- Every file references only real paths, commands, and conventions from this project.
- Types are correct per Step 2; no task-shaped instructions, no always-on skills.
- Frontmatter is valid; prompts use `${input:...}`; instructions are narrowly scoped; skills have "Use when:" triggers; agents have minimal tool lists matching their permissions.
- Related items across types are intentional and complementary (e.g. an instruction for the *rules*, a prompt to *do the task once*, an agent for the *ongoing role*).
