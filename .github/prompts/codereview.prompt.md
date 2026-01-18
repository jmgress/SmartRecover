---
mode: agent
---

# Comprehensive Code Review Assistant

Please conduct a thorough code review of the provided code, analyzing it against the Quizly project's architecture and best practices. Provide actionable feedback with specific examples and improvement suggestions.

## Core Review Principles

### Code Quality Standards
- **Clean Code**: Follow SOLID principles, DRY, and KISS patterns
- **Readability**: Clear, self-documenting code with descriptive names
- **Maintainability**: Modular design with proper separation of concerns
- **Performance**: Efficient algorithms and resource usage
- **Testing**: Adequate test coverage with meaningful test cases

### Architecture Alignment
- **Backend**: FastAPI patterns, SQLite best practices, modular LLM provider design  
- **Frontend**: React best practices, component composition, state management
- **API Design**: RESTful conventions, proper HTTP status codes, error handling
- **Database**: Normalized schema, indexed queries, transaction management
- **Configuration**: Centralized config management, environment separation

## Detailed Review Areas

### 1. Security Analysis
**Critical Security Checks:**
- [ ] Input validation and sanitization (XSS, injection prevention)
- [ ] SQL injection protection via parameterized queries
- [ ] Authentication and authorization implementation
- [ ] Sensitive data handling (no secrets in logs/errors)
- [ ] CORS configuration and API endpoint security
- [ ] Path traversal protection (especially in logging system)
- [ ] Dependency vulnerability assessment
- [ ] Error message information disclosure

**Quizly-Specific Security:**
- [ ] LLM provider API key security and rotation
- [ ] Admin interface access controls
- [ ] Quiz data integrity and user session management
- [ ] Log file access restrictions and sensitive data filtering

### 2. Backend Code Review (Python/FastAPI)

**API Endpoints:**
- [ ] Proper HTTP methods and status codes
- [ ] Request/response validation with Pydantic models
- [ ] Error handling with appropriate exception types
- [ ] Rate limiting and input size restrictions
- [ ] Async/await usage for I/O operations

**Database Operations:**
- [ ] Connection pooling and resource cleanup
- [ ] Transaction boundaries and rollback handling
- [ ] Query optimization and indexing
- [ ] Data migration and schema versioning
- [ ] Backup and recovery considerations

**LLM Provider Integration:**
- [ ] Provider abstraction and interface consistency
- [ ] Error handling for external API failures
- [ ] Timeout and retry logic implementation
- [ ] Cost tracking and usage monitoring
- [ ] Provider switching mechanism reliability

**Example Issues to Flag:**
```python
# ❌ BAD: Vulnerable to SQL injection
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ GOOD: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### 3. Frontend Code Review (React/JavaScript)

**Component Design:**
- [ ] Single responsibility principle adherence
- [ ] Proper prop validation with PropTypes or TypeScript
- [ ] State management efficiency (useState, useEffect usage)
- [ ] Component lifecycle optimization
- [ ] Accessibility (ARIA attributes, keyboard navigation)

**Performance Considerations:**
- [ ] Unnecessary re-renders prevention
- [ ] Bundle size optimization
- [ ] Image and asset optimization
- [ ] API call efficiency and caching
- [ ] Memory leak prevention

**User Experience:**
- [ ] Loading states and error boundaries
- [ ] Responsive design implementation
- [ ] Form validation and user feedback
- [ ] Navigation and routing logic

**Example Issues to Flag:**
```javascript
// ❌ BAD: Missing dependency array causing infinite loops
useEffect(() => {
  fetchData();
});

// ✅ GOOD: Proper dependency management
useEffect(() => {
  fetchData();
}, [dependency]);
```

### 4. Testing Code Review

**Test Quality:**
- [ ] Arrange-Act-Assert pattern usage
- [ ] Test isolation and independence
- [ ] Meaningful test names and descriptions
- [ ] Edge case and error condition coverage
- [ ] Mock usage appropriateness

**Coverage Analysis:**
- [ ] Critical path testing completeness
- [ ] Integration test scenarios
- [ ] End-to-end workflow validation
- [ ] Security test cases inclusion

**Quizly-Specific Testing:**
- [ ] LLM provider mocking and integration tests
- [ ] Quiz generation and scoring logic validation
- [ ] Admin interface functionality testing
- [ ] Logging system behavior verification

### 5. Configuration and Infrastructure

**Configuration Management:**
- [ ] Environment-specific settings separation
- [ ] Sensitive configuration protection
- [ ] Default value appropriateness
- [ ] Configuration validation and error handling

**Logging and Monitoring:**
- [ ] Appropriate log levels usage
- [ ] Structured logging implementation
- [ ] Log rotation and retention policies
- [ ] Performance metrics collection

**Deployment Considerations:**
- [ ] Build process optimization
- [ ] Dependency management and pinning
- [ ] Health check endpoint implementation
- [ ] Graceful shutdown handling

## Review Output Format

For each identified issue, provide:

### 1. Issue Classification
- **Severity**: Critical, High, Medium, Low
- **Category**: Security, Performance, Maintainability, Bug, Style
- **Impact**: User experience, system stability, security risk

### 2. Detailed Analysis
- **Current Implementation**: What the code currently does
- **Problem**: Why it's problematic
- **Risk**: Potential consequences if not addressed
- **Solution**: Specific improvement recommendations with code examples

### 3. Code Examples
```python
# Current code (problematic)
def problematic_function():
    # explain the issue
    pass

# Suggested improvement
def improved_function():
    # explain the improvement
    pass
```

### 4. Priority Recommendations
1. **Immediate**: Security vulnerabilities and critical bugs
2. **Short-term**: Performance issues and major maintainability concerns
3. **Long-term**: Code organization and minor optimizations

## Contextual Considerations

### Project-Specific Patterns
- **LLM Provider Architecture**: Evaluate provider abstraction consistency
- **Configuration System**: Review centralized config management usage
- **Logging Framework**: Assess structured logging implementation
- **Security Scanning**: Consider GitLeaks integration and secret management

### Development Workflow
- **CI/CD Integration**: Review automated testing and deployment scripts
- **Code Organization**: Evaluate file structure and module organization
- **Documentation**: Assess code documentation quality and completeness
- **Error Handling**: Review error propagation and user-facing messages

Please provide a comprehensive analysis that helps maintain Quizly's high code quality standards while identifying opportunities for improvement and potential risks that need immediate attention.