# Knowledge Base Runbooks

This directory contains sample runbook files for the Knowledge Base Agent when running in mock mode.

## Purpose

These markdown files serve as documentation and troubleshooting guides that the Knowledge Base Agent can search and retrieve when helping to resolve incidents.

## File Format

Runbooks should be written in Markdown format (`.md` or `.txt` files). They can optionally include YAML frontmatter for metadata:

```markdown
---
title: My Runbook Title
---

# Runbook Content

Your troubleshooting steps and documentation here...
```

## How It Works

When the Knowledge Base Agent is configured in mock mode with a `docs_folder` setting, it will:

1. Load all `.md` and `.txt` files from this directory
2. Extract titles from frontmatter or generate them from filenames
3. Index the content for keyword-based searching
4. Return relevant documents when queried

## Configuration

To enable runbook loading, configure the Knowledge Base Agent in `config.yaml`:

```yaml
knowledge_base:
  source: "mock"
  mock:
    csv_path: "backend/data/csv/confluence_docs.csv"
    docs_folder: "backend/data/runbooks/"  # Enable runbook loading
```

Or via environment variable:

```bash
export KB_DOCS_FOLDER="backend/data/runbooks/"
```

## Adding New Runbooks

1. Create a new `.md` file in this directory
2. Optionally add YAML frontmatter with a title
3. Write your troubleshooting steps and documentation
4. The Knowledge Base Agent will automatically load it on initialization

## Sample Runbooks

This directory includes sample runbooks for:

- Database Connection Troubleshooting
- API Gateway Performance Issues
- Authentication Service Problems

Feel free to add more runbooks specific to your infrastructure and common incident patterns.
