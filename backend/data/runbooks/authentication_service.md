---
title: Authentication Service Issues
---

# Authentication Service Troubleshooting

## Overview
Guide for diagnosing and resolving authentication service problems.

## Common Issues

### Login Failures
**Symptoms:** Users unable to login, 401/403 errors

**Causes:**
- Token expiration
- Invalid credentials
- Session store issues
- Authentication service downtime

**Resolution:**
1. Check authentication service health
2. Verify session store connectivity (Redis)
3. Review token configuration
4. Check for expired certificates

### Token Refresh Problems
**Symptoms:** Frequent logouts, token refresh failures

**Resolution:**
1. Review token TTL settings
2. Check refresh token rotation
3. Verify clock synchronization

### SSO Integration Issues
**Symptoms:** SSO login redirects fail, SAML errors

**Resolution:**
1. Verify SSO provider configuration
2. Check certificate validity
3. Review SAML assertion format
4. Test IdP connectivity

## Quick Fixes

### Clear Session Cache
```bash
redis-cli FLUSHDB
```

### Restart Auth Service
```bash
kubectl rollout restart deployment/auth-service
```

### Check Service Logs
```bash
kubectl logs -f deployment/auth-service --tail=100
```

## Monitoring
- Login success/failure rates
- Token validation latency
- Session store hit rate
- SSO provider response time
