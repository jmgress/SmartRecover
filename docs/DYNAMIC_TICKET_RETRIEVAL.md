# Dynamic Related Ticket Retrieval

## Overview

This feature implements **runtime discovery of related ServiceNow tickets** based on similarity to past resolved incidents. Instead of using hardcoded ticket relationships, the system dynamically finds similar incidents by analyzing their characteristics.

## How It Works

### Similarity Algorithm

The system uses a multi-factor similarity algorithm to match incidents:

1. **Text Similarity** (Jaccard Coefficient)
   - Extracts keywords from incident titles and descriptions
   - Removes common stopwords
   - Calculates overlap between keyword sets
   
2. **Service Similarity** (Jaccard Coefficient)
   - Compares affected services between incidents
   - Measures service overlap
   
3. **Weighted Scoring**
   - Title similarity: 40%
   - Description similarity: 40%
   - Service similarity: 20%

### Matching Process

When querying for related tickets:

1. Find the current incident by ID
2. Search all **resolved** incidents for similar ones
3. Calculate similarity scores for each incident
4. Filter by similarity threshold (default: 0.2)
5. Sort by similarity score (descending)
6. Return top N results (default: 5)
7. Exclude the current incident itself

### Example

```python
from backend.agents.servicenow_agent import ServiceNowAgent
import asyncio

async def find_similar():
    agent = ServiceNowAgent(
        similarity_threshold=0.2,
        max_results=5
    )
    
    result = await agent.query("INC001", "database timeout issues")
    
    for ticket in result['similar_incidents']:
        print(f"Ticket: {ticket['ticket_id']}")
        print(f"From: {ticket['source_incident_title']}")
        print(f"Similarity: {ticket['similarity_score']:.3f}")
        print(f"Resolution: {ticket['resolution']}")
        print()

asyncio.run(find_similar())
```

### Real Output Example

```
Testing INC001 (Database connection timeout):
  Similar incidents found: 2
    1. SNOW011: Redis cache connection failures (score: 0.202)
       Resolution: Increased Redis connection pool and added circuit breaker pattern
    2. JIRA-127: Redis cache connection failures (score: 0.202)
       Resolution: Implemented Redis sentinel for automatic failover
```

## Configuration

### ServiceNowAgent Parameters

```python
ServiceNowAgent(
    similarity_threshold=0.2,  # Minimum similarity score (0.0-1.0)
    max_results=5              # Maximum similar incidents to return
)
```

### MockConnector Parameters

```python
MockConnector({
    "similarity_threshold": 0.2,
    "max_similar_incidents": 5
})
```

## Key Features

### ✅ Dynamic Matching
- No hardcoded incident relationships required
- Automatically finds similar past incidents
- Updates as new resolved incidents are added

### ✅ Only Resolved Incidents
- Only considers incidents with `status=resolved`
- Ensures historical context is complete
- Prevents matching against active incidents

### ✅ Self-Exclusion
- Current incident never matches itself
- Avoids circular references

### ✅ Configurable Thresholds
- Adjust sensitivity via `similarity_threshold`
- Control result count via `max_results`

### ✅ Rich Metadata
Each matched ticket includes:
- `similarity_score`: Confidence level (0.0-1.0)
- `source_incident_id`: ID of the matched incident
- `source_incident_title`: Title for context
- `resolution`: Solution that worked before

## Implementation Files

### Core Algorithm
- `backend/utils/similarity.py` - Similarity calculation functions
  - Text normalization and keyword extraction
  - Jaccard similarity coefficients
  - Incident comparison logic

### Integration Points
- `backend/connectors/mock_connector.py` - MockConnector implementation
- `backend/agents/servicenow_agent.py` - ServiceNow agent with dynamic retrieval

### Tests
- `backend/tests/test_similarity.py` - 23 tests for similarity algorithms
- `backend/tests/test_dynamic_retrieval.py` - 17 tests for connector/agent integration
- `backend/tests/test_mock_data.py` - 21 backward compatibility tests

## Performance Considerations

### Time Complexity
- **Per Query**: O(n × m) where:
  - n = number of resolved incidents
  - m = average keywords per incident
  
### Optimization Opportunities
For production with large datasets:
1. **Pre-compute embeddings** - Use sentence transformers
2. **Vector database** - Store embeddings in Pinecone/Weaviate
3. **Caching** - Cache similarity scores for common queries
4. **Indexing** - Create inverted index on keywords

### Current Approach
The current implementation prioritizes:
- **Simplicity** - No external dependencies
- **Transparency** - Clear scoring methodology  
- **Testability** - Deterministic results

## Future Enhancements

### Short Term
- [ ] Add incident severity weighting
- [ ] Include creation date recency in scoring
- [ ] Support partial keyword matching (fuzzy)

### Medium Term
- [ ] Integrate with real ServiceNow API
- [ ] Add machine learning-based similarity
- [ ] Implement result caching

### Long Term
- [ ] Use LLM embeddings for semantic similarity
- [ ] Support multi-language incidents
- [ ] Add user feedback loop for relevance tuning

## Testing

Run all tests:
```bash
cd backend
pytest tests/test_similarity.py tests/test_dynamic_retrieval.py -v
```

Run with coverage:
```bash
pytest tests/test_similarity.py tests/test_dynamic_retrieval.py --cov=backend.utils.similarity --cov=backend.connectors.mock_connector --cov=backend.agents.servicenow_agent
```

## References

- **Jaccard Similarity**: https://en.wikipedia.org/wiki/Jaccard_index
- **Text Similarity Methods**: https://www.elastic.co/blog/text-similarity-search-with-vectors-in-elasticsearch
- **Incident Correlation**: https://www.atlassian.com/incident-management/kpis/incident-correlation
