# CI/CD Documentation for SmartRecover

This document describes the Continuous Integration and Continuous Deployment (CI/CD) automation setup for the SmartRecover project.

## Overview

SmartRecover uses GitHub Actions for automated testing, linting, and security scanning. The CI/CD pipeline ensures code quality, security, and reliability before merging changes.

## Workflows

### 1. Secret Scanning (`secret-scanning.yml`)

**Purpose**: Detects exposed secrets and sensitive information in the codebase.

**Tool**: [Gitleaks](https://github.com/gitleaks/gitleaks)

**Triggers**:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Daily scheduled scan at 2 AM UTC

**What it checks**:
- API keys (OpenAI, Google, custom)
- Passwords and tokens
- Private keys and certificates
- Database connection strings

**Configuration**: `.gitleaks.toml` at repository root

**How to fix failures**:
1. Remove the secret from your code
2. Add the file/pattern to `.gitleaks.toml` allowlist if it's a false positive
3. Rotate the exposed secret immediately if it was real

### 2. CI Pipeline (`ci.yml`)

The main CI pipeline runs three parallel jobs followed by a build verification.

#### Job 1: Backend Linting

**Purpose**: Ensures Python code follows style guidelines and best practices.

**Tool**: [Ruff](https://docs.astral.sh/ruff/) - Fast Python linter and formatter

**What it checks**:
- Code style (PEP 8)
- Import sorting
- Common bugs and anti-patterns
- Code formatting

**Configuration**: `backend/ruff.toml`

**Running locally**:
```bash
# Install Ruff
pip install ruff

# Run linter
cd backend
ruff check .

# Check formatting
ruff format --check .

# Auto-fix issues
ruff check --fix .
ruff format .
```

#### Job 2: Backend Tests

**Purpose**: Runs Python tests with coverage reporting.

**Tool**: pytest with pytest-cov

**What it does**:
- Runs all tests in `backend/tests/`
- Generates coverage report
- Uploads coverage to Codecov

**Configuration**: `backend/pytest.ini`

**Running locally**:
```bash
cd backend

# Install dependencies
pip install -r requirements.txt
pip install pytest-cov

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=xml --cov-report=term

# Run specific test file
pytest tests/test_knowledge_base.py -v
```

**Coverage thresholds**:
- Current: Report only (no enforcement)
- Future: May add minimum coverage requirements

#### Job 3: Frontend Tests

**Purpose**: Runs React/TypeScript tests with coverage reporting.

**Tool**: Jest (via Create React App)

**What it does**:
- Runs all tests in `frontend/src/`
- Generates coverage report
- Uploads coverage to Codecov

**Running locally**:
```bash
cd frontend

# Install dependencies
npm install

# Run tests with coverage
CI=true npm test -- --coverage --watchAll=false

# Run tests in watch mode (development)
npm test

# Run specific test file
npm test -- App.test.tsx
```

#### Job 4: Build Check

**Purpose**: Verifies that the application builds successfully.

**What it does**:
- Installs all dependencies
- Builds the frontend React app
- Verifies build artifacts exist

**Running locally**:
```bash
# Build frontend
cd frontend
npm run build

# Start production build locally
npx serve -s build
```

## Code Coverage with Codecov

SmartRecover uses [Codecov](https://about.codecov.io/) to track test coverage across backend and frontend.

### Setup

1. **Codecov Token**: Add `CODECOV_TOKEN` to repository secrets
   - Go to: Repository Settings → Secrets and variables → Actions
   - Add new secret: `CODECOV_TOKEN`
   - Get token from: https://codecov.io/gh/jmgress/SmartRecover

2. **Coverage Reports**: Automatically uploaded after test runs
   - Backend: `backend/coverage.xml`
   - Frontend: `frontend/coverage/lcov.info`

3. **Flags**: Coverage is tracked separately for backend and frontend

### Viewing Coverage Reports

**On Codecov.io**:
- Visit: https://codecov.io/gh/jmgress/SmartRecover
- View coverage trends, file-by-file coverage, and pull request impact

**In Pull Requests**:
- Codecov bot comments with coverage changes
- Shows if coverage increased or decreased

**Locally**:
```bash
# Backend - HTML report
cd backend
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# Frontend - HTML report
cd frontend
npm test -- --coverage --watchAll=false
open coverage/lcov-report/index.html
```

## CI/CD Best Practices

### For Developers

1. **Run tests locally before pushing**:
   ```bash
   ./test.sh --all
   ```

2. **Fix linting issues before committing**:
   ```bash
   cd backend
   ruff check --fix .
   ruff format .
   ```

3. **Check for secrets before committing**:
   ```bash
   # Install Gitleaks locally
   brew install gitleaks  # macOS
   # or download from: https://github.com/gitleaks/gitleaks/releases
   
   # Run scan
   gitleaks detect --source . -v
   ```

4. **Review coverage reports**:
   - Aim to maintain or increase coverage
   - Add tests for new features
   - Don't remove tests to increase coverage

### For Maintainers

1. **Required Status Checks**:
   - Enable branch protection on `main` and `develop`
   - Require CI checks to pass before merging
   - Require up-to-date branches

2. **Secret Management**:
   - Never commit secrets to the repository
   - Use GitHub Secrets for sensitive values
   - Rotate secrets immediately if exposed

3. **Monitoring**:
   - Check Codecov dashboard regularly
   - Review failed workflow runs
   - Update dependencies when security alerts appear

## Troubleshooting

### Common Issues

#### "Linting failed"
```bash
# Fix automatically
cd backend
ruff check --fix .
ruff format .
```

#### "Tests failed"
```bash
# Run tests locally to debug
cd backend
pytest tests/ -v -x  # Stop at first failure

# Run with more detail
pytest tests/test_knowledge_base.py -vv -s
```

#### "Secret detected"
1. Check the workflow logs for the detected secret
2. Remove it from the code
3. Add false positives to `.gitleaks.toml` allowlist
4. Rotate the secret if it was real

#### "Coverage upload failed"
- Ensure `CODECOV_TOKEN` is set in repository secrets
- Check if Codecov.io is accessible
- Verify coverage files are generated

#### "Node modules installation failed"
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## GitHub Actions Limits

**Free tier limits** (public repositories):
- Unlimited minutes per month
- 20 concurrent jobs

**Tips to optimize**:
- Use caching for dependencies (already configured)
- Run jobs in parallel where possible
- Cancel outdated workflow runs

## Adding New Checks

### Adding a New Linter

1. Update `ci.yml` to add a new job:
```yaml
new-linter:
  name: New Linter
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Run linter
      run: |
        # Your linter commands
```

2. Add configuration file if needed
3. Update this documentation

### Adding Security Scanning

Consider adding:
- **Dependabot**: Automated dependency updates (GitHub native)
- **CodeQL**: Code security scanning (GitHub native)
- **Snyk**: Vulnerability scanning for dependencies

### Adding Deployment

For automated deployment, add:
1. Deployment job in `ci.yml`
2. Environment secrets for deployment
3. Deployment documentation

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [Codecov Documentation](https://docs.codecov.com/)
- [Gitleaks Documentation](https://github.com/gitleaks/gitleaks)

## Questions?

For questions about CI/CD setup, please:
1. Check this documentation
2. Review workflow logs in GitHub Actions tab
3. Open an issue with the `ci-cd` label
