# Secret Scanning

SmartRecover uses automated secret scanning to prevent accidental exposure of sensitive credentials and API keys.

## Overview

The repository is protected by a GitHub Actions workflow that scans for secrets on every push and pull request. This helps ensure that no sensitive information (API keys, passwords, tokens, etc.) is accidentally committed to the repository.

## How It Works

### Automated Scanning

The secret scanning workflow (`.github/workflows/secret-scan.yml`) runs automatically:

- **On Push**: When code is pushed to `main` or `develop` branches
- **On Pull Request**: When a PR is opened or updated against `main` or `develop`
- **Manual Trigger**: Can be manually triggered from the GitHub Actions tab

### Scanning Tool

We use [TruffleHog](https://github.com/trufflesecurity/trufflehog) for secret detection because it:

- Scans entire git history, not just current files
- Detects over 700 types of secrets (API keys, tokens, passwords, etc.)
- Verifies secrets by attempting to authenticate with them (when possible)
- Has very low false positive rates
- Is actively maintained and widely trusted

### What Gets Scanned

TruffleHog scans:

- All source code files (`.py`, `.js`, `.ts`, `.tsx`, `.yaml`, `.yml`, etc.)
- Configuration files
- Git commit history
- Environment variable files (if accidentally committed)

### What's Protected

The following files are already in `.gitignore` and won't be committed:

- `.env` - Local environment variables
- `.env.local`, `.env.development.local`, etc.
- Any files with actual credentials

## Best Practices

### Do's ✅

1. **Use Environment Variables**: Always store secrets in environment variables
   ```python
   import os
   api_key = os.getenv("OPENAI_API_KEY")
   ```

2. **Use `.env.example`**: Provide example configuration with placeholders
   ```bash
   # .env.example
   OPENAI_API_KEY=your-api-key-here
   ```

3. **Document Required Variables**: List all required environment variables in README

4. **Use Secret Management**: For production, use proper secret management (AWS Secrets Manager, Azure Key Vault, etc.)

### Don'ts ❌

1. **Don't Hardcode Secrets**: Never hardcode API keys or passwords
   ```python
   # ❌ BAD
   api_key = "sk-1234567890abcdef"
   
   # ✅ GOOD
   api_key = os.getenv("OPENAI_API_KEY")
   ```

2. **Don't Commit `.env` Files**: These should always be in `.gitignore`

3. **Don't Share Secrets in Issues/PRs**: Never paste actual secrets in GitHub issues or PRs

4. **Don't Use Weak Placeholders**: Don't use realistic-looking fake keys that might trigger scanners

## If Secrets Are Detected

If the secret scan fails, follow these steps:

### 1. Identify the Secret

Review the GitHub Actions log to see which secret was detected and in which file.

### 2. Remove the Secret

If it's a current commit:
```bash
# Remove the secret from the file
# Then commit the fix
git add .
git commit -m "Remove exposed secret"
git push
```

### 3. Rotate the Secret

**Important**: If a real secret was committed, assume it's compromised:

1. **Immediately revoke/rotate** the exposed credential
2. Generate a new key/token
3. Update your local `.env` file with the new secret
4. Update any production secret managers

### 4. Clean Git History (if needed)

If the secret is in git history (not just the latest commit):

```bash
# Use BFG Repo-Cleaner or git-filter-repo to remove from history
# See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
```

## False Positives

If TruffleHog flags a false positive (e.g., example code, test data):

1. Add the pattern to `.trufflehog-ignore` file:
   ```
   # Example test key that's not real
   test-key-placeholder-not-real
   ```

2. Commit the updated ignore file
3. Re-run the workflow

## Testing the Workflow

To manually test the secret scanning:

1. Go to the **Actions** tab in GitHub
2. Select **Secret Scanning** workflow
3. Click **Run workflow**
4. Select the branch and click **Run workflow**

## Integration with Development

### Pre-commit Hook (Optional)

You can install TruffleHog locally to scan before committing:

```bash
# Install TruffleHog
brew install trufflesecurity/trufflehog/trufflehog
# or
pip install trufflehog

# Scan before committing
trufflehog filesystem . --only-verified
```

### Local Scanning

To scan your local repository:

```bash
# Scan git history
trufflehog git file://. --only-verified

# Scan filesystem (uncommitted changes)
trufflehog filesystem . --only-verified
```

## Configuration

The workflow configuration is in `.github/workflows/secret-scan.yml`:

- **Branches**: Scans `main` and `develop` by default
- **Trigger**: Runs on push, pull requests, and manual trigger
- **Options**: Uses `--only-verified` to reduce false positives

To modify:
1. Edit `.github/workflows/secret-scan.yml`
2. Commit and push changes
3. The updated workflow will be used on the next run

## Application Code Changes

**No application code changes are required** when adding secret scanning. The workflow operates at the CI/CD level and doesn't affect application functionality. However, your application should already follow best practices:

- ✅ **Already Implemented**: SmartRecover reads all secrets from environment variables
- ✅ **Already Implemented**: `.env` file is in `.gitignore`
- ✅ **Already Implemented**: `.env.example` contains only placeholders
- ✅ **Already Implemented**: No hardcoded secrets in source code

## Resources

- [TruffleHog Documentation](https://github.com/trufflesecurity/trufflehog)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Best Practices for Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
