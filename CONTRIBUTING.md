# Contributing to SmartRecover

Thank you for contributing to SmartRecover! This guide will help you set up your development environment and ensure your contributions pass all CI checks.

## Quick Start for Contributors

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/SmartRecover.git
cd SmartRecover
```

### 2. Set Up Development Environment

#### Backend Setup

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

#### Frontend Setup

```bash
cd frontend
npm install
```

### 3. Make Your Changes

Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

### 4. Run Tests and Linting Locally

Before pushing your changes, ensure all checks pass:

#### Backend Checks

```bash
cd backend

# Run linting
ruff check .
ruff format --check .

# Auto-fix linting issues
ruff check --fix .
ruff format .

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=term
```

#### Frontend Checks

```bash
cd frontend

# Run tests with coverage
CI=true npm test -- --coverage --watchAll=false

# Run tests in watch mode (for development)
npm test
```

#### All Tests at Once

```bash
# From the repository root
./test.sh
```

### 5. Commit and Push

```bash
git add .
git commit -m "Description of your changes"
git push origin feature/your-feature-name
```

### 6. Create a Pull Request

1. Go to the [SmartRecover repository](https://github.com/jmgress/SmartRecover)
2. Click "New Pull Request"
3. Select your branch
4. Fill in the PR description with:
   - What changes you made
   - Why you made them
   - Any testing you performed

## CI/CD Pipeline

When you create a pull request, the following checks will run automatically:

### 1. Secret Scanning
- **Tool**: Gitleaks
- **Purpose**: Ensures no secrets or credentials are committed
- **Fix**: Remove any secrets and use environment variables instead

### 2. Backend Linting
- **Tool**: Ruff
- **Purpose**: Ensures Python code follows style guidelines
- **Fix**: Run `ruff check --fix .` and `ruff format .` in the backend directory

### 3. Backend Tests
- **Tool**: pytest
- **Coverage Target**: Maintain or increase coverage (currently 78%)
- **Fix**: Ensure your new code is tested and all tests pass

### 4. Frontend Tests
- **Tool**: Jest
- **Coverage Target**: Maintain or increase coverage (currently 30%)
- **Fix**: Ensure your new components/functions are tested

### 5. Build Check
- **Purpose**: Verifies the application builds successfully
- **Fix**: Test the build locally with `npm run build` in the frontend directory

## Code Style Guidelines

### Python (Backend)

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep functions focused and small
- Add docstrings to classes and functions
- Use meaningful variable names
- Ruff will enforce most style rules automatically

### TypeScript/React (Frontend)

- Use functional components with hooks
- Follow React best practices
- Use TypeScript for type safety
- Keep components small and reusable
- Add tests for new components and hooks

## Testing Guidelines

### Backend Testing

- Write tests for all new features
- Use pytest fixtures for test setup
- Test both success and error cases
- Mock external dependencies
- Aim for at least 80% coverage for new code

Example test structure:
```python
import pytest
from backend.your_module import your_function

def test_your_function_success():
    """Test successful case."""
    result = your_function("valid_input")
    assert result == expected_output

def test_your_function_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        your_function("invalid_input")
```

### Frontend Testing

- Write tests for new components
- Test user interactions
- Test hooks and custom logic
- Use React Testing Library best practices
- Aim for meaningful coverage

Example test structure:
```typescript
import { render, screen } from '@testing-library/react';
import YourComponent from './YourComponent';

test('renders component correctly', () => {
  render(<YourComponent />);
  const element = screen.getByText(/expected text/i);
  expect(element).toBeInTheDocument();
});
```

## Common Issues and Fixes

### "Linting failed"

```bash
cd backend
ruff check --fix .
ruff format .
```

### "Tests failed"

```bash
# Run tests with verbose output to see which test failed
cd backend
pytest tests/ -v -x  # -x stops at first failure

# Run specific test file
pytest tests/test_your_file.py -vv
```

### "Secret detected"

1. Identify the secret in the logs
2. Remove it from your code
3. Add it to `.env.example` as a placeholder
4. Use environment variables in your code
5. Never commit real secrets

### "Coverage decreased"

- Add tests for your new code
- Ensure your tests actually execute the new code paths
- Run coverage locally: `pytest tests/ --cov=. --cov-report=html`
- Open `htmlcov/index.html` to see which lines need coverage

## Getting Help

- **Documentation**: Check [docs/CI_CD.md](docs/CI_CD.md) for detailed CI/CD information
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions

## Pre-commit Checklist

Before creating a pull request, ensure:

- [ ] All tests pass locally (`./test.sh`)
- [ ] Code is properly formatted (`ruff format .` for backend)
- [ ] No linting errors (`ruff check .` for backend)
- [ ] No secrets in the code
- [ ] New code has tests
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive

## Review Process

1. Automated CI checks must pass
2. Code review by maintainers
3. Approval and merge

Thank you for contributing to SmartRecover! 🎉
