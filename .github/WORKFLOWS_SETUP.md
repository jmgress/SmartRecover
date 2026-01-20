# GitHub Actions Setup Guide

This document describes the setup process for SmartRecover's GitHub Actions workflows.

## Required Secrets

To enable all CI/CD features, you need to configure the following secrets in your GitHub repository:

### Setting up secrets

Navigate to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

### Required Secrets

#### CODECOV_TOKEN (Required for coverage reporting)
1. Sign up at [codecov.io](https://codecov.io/)
2. Link your GitHub repository
3. Copy the upload token
4. Add as `CODECOV_TOKEN` secret in GitHub

#### GITLEAKS_LICENSE (Optional - for enterprise features)
- Only needed if you have a Gitleaks Enterprise license
- The free version works without this secret

## Workflows Overview

### 1. Secrets Scan (`secrets-scan.yml`)
**Trigger**: Push to main, PRs to main, manual dispatch  
**Purpose**: Detect accidentally committed secrets  
**Tool**: [Gitleaks](https://github.com/gitleaks/gitleaks)

**What it scans:**
- API keys
- Passwords
- Private keys
- Database connection strings
- OAuth tokens
- AWS credentials
- And more...

### 2. CI Workflow (`ci.yml`)
**Trigger**: Push to main, PRs to main, manual dispatch  
**Purpose**: Automated testing, linting, and coverage

**Jobs:**
- **Backend Linting**: Ruff linter and formatter checks
- **Backend Tests**: pytest with coverage reporting
- **Frontend Tests**: Jest with coverage reporting

All jobs run in parallel for faster feedback.

## Local Testing

### Run linting locally:
```bash
cd backend
pip install ruff
ruff check .
ruff format --check .
```

### Run tests with coverage locally:
```bash
# Backend
cd backend
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html

# Frontend
cd frontend
npm test -- --coverage
```

### Scan for secrets locally:
```bash
# Install gitleaks (macOS)
brew install gitleaks

# Or download from https://github.com/gitleaks/gitleaks/releases

# Run scan
gitleaks detect --source . --verbose
```

## Troubleshooting

### Codecov upload fails
- Verify `CODECOV_TOKEN` is set correctly
- Check that coverage files are being generated
- Ensure the token has write permissions

### Linting fails
- Run `ruff check . --fix` locally to auto-fix issues
- Some issues may require manual intervention
- Check `backend/pyproject.toml` for configuration

### Tests fail
- Run tests locally first: `./test.sh`
- Check for environment-specific issues
- Verify all dependencies are in requirements.txt/package.json

## Status Badges

Once workflows run successfully, you can add badges to your README:

```markdown
[![CI](https://github.com/jmgress/SmartRecover/actions/workflows/ci.yml/badge.svg)](https://github.com/jmgress/SmartRecover/actions/workflows/ci.yml)
[![Secrets Scan](https://github.com/jmgress/SmartRecover/actions/workflows/secrets-scan.yml/badge.svg)](https://github.com/jmgress/SmartRecover/actions/workflows/secrets-scan.yml)
[![codecov](https://codecov.io/gh/jmgress/SmartRecover/branch/main/graph/badge.svg)](https://codecov.io/gh/jmgress/SmartRecover)
```
