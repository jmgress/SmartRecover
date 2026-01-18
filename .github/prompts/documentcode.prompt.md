---
mode: agent
---

# Code Documentation Assistant

Please analyze and document the provided code with comprehensive, clear, and maintainable documentation following these guidelines:

## Documentation Standards

### Python Code (Backend/Tests)
- **Docstrings**: Use Google-style docstrings for all functions, classes, and modules
- **Type hints**: Include type annotations for parameters and return values
- **Error handling**: Document expected exceptions and error conditions
- **Examples**: Provide usage examples for complex functions or API endpoints
- **Security notes**: Highlight security considerations, especially for authentication/authorization code

### JavaScript/React Code (Frontend)
- **JSDoc comments**: Use JSDoc format for functions and components
- **Component props**: Document all React component props with types and descriptions
- **State management**: Explain complex state logic and data flow
- **Event handlers**: Document user interactions and their effects
- **API calls**: Document backend API integrations and error handling

### Configuration Files
- **Purpose**: Explain the file's role in the application
- **Key settings**: Document important configuration options
- **Environment dependencies**: Note environment-specific settings
- **Security implications**: Highlight sensitive configuration values

## Project-Specific Context

### Quizly Architecture Awareness
- **Backend**: FastAPI with SQLite, modular LLM provider system
- **Frontend**: React with REST API communication
- **LLM Integration**: Document AI question generation logic and provider switching
- **Logging**: Explain logging configuration and path traversal protection
- **Security**: Note GitLeaks integration and security scanning considerations

### Key Documentation Areas
1. **API Endpoints**: Document request/response schemas, authentication requirements
2. **Database Models**: Explain entity relationships and constraints
3. **LLM Providers**: Document provider interfaces and configuration requirements
4. **Test Code**: Explain test scenarios, fixtures, and mock usage
5. **Config Management**: Document centralized configuration patterns

## Documentation Format

### Function/Method Documentation
```python
def generate_quiz_questions(topic: str, difficulty: str, count: int) -> List[Dict]:
    """Generate quiz questions using the configured LLM provider.
    
    Args:
        topic: The subject matter for questions
        difficulty: Question difficulty level ('easy', 'medium', 'hard')
        count: Number of questions to generate (1-20)
        
    Returns:
        List of question dictionaries with keys: 'question', 'options', 'correct_answer'
        
    Raises:
        ValueError: If count is outside valid range
        LLMProviderError: If AI service is unavailable
        
    Example:
        >>> questions = generate_quiz_questions("Python", "medium", 5)
        >>> len(questions)
        5
    """
```

### Class Documentation
```python
class QuizManager:
    """Manages quiz creation, storage, and retrieval.
    
    This class handles the complete quiz lifecycle including question generation
    via LLM providers, database persistence, and score tracking. It implements
    the repository pattern for data access.
    
    Attributes:
        db_connection: SQLite database connection
        llm_provider: Current AI provider instance
        
    Security:
        All database queries use parameterized statements to prevent SQL injection.
    """
```

### React Component Documentation
```javascript
/**
 * Quiz component for displaying interactive questions to users.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Array<Object>} props.questions - Array of question objects
 * @param {Function} props.onComplete - Callback when quiz is finished
 * @param {string} props.difficulty - Quiz difficulty level
 * @param {boolean} [props.showHints=false] - Whether to show question hints
 * 
 * @example
 * <Quiz 
 *   questions={quizData} 
 *   onComplete={handleQuizComplete}
 *   difficulty="medium"
 *   showHints={true}
 * />
 */
```

## Quality Guidelines

- **Clarity**: Write for developers who are new to the codebase
- **Completeness**: Cover all important aspects without being verbose
- **Accuracy**: Ensure documentation matches actual code behavior
- **Maintenance**: Keep documentation close to the code it describes
- **Context**: Explain "why" decisions were made, not just "what" the code does
- **Integration**: Reference related components, APIs, and configuration files

## Special Considerations

- **Test Documentation**: Explain test scenarios and expected outcomes
- **Error Handling**: Document error conditions and recovery strategies
- **Performance**: Note any performance implications or optimizations
- **Security**: Highlight authentication, authorization, and data protection measures
- **Configuration**: Explain environment-dependent behavior and setup requirements

Please apply these standards to create comprehensive, maintainable documentation that helps developers understand, use, and contribute to the Quizly codebase effectively.

