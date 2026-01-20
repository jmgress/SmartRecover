# Mock Data Generator

This directory contains a reusable script for generating realistic mock data for SmartRecover testing and development.

## Quick Start

Generate 10x the current data (150 incidents):
```bash
python generate_mock_data.py --scale 10 --preserve-existing
```

Generate a specific number of incidents:
```bash
python generate_mock_data.py --incidents 200
```

## Features

### 1. Reusable Data Generation Script
- **Script**: `generate_mock_data.py`
- **Purpose**: Generate realistic mock data at any scale
- **Benefits**: 
  - Reproducible data generation with seed control
  - Consistent data patterns and relationships
  - Configurable scale factor

### 2. Lazy Loading Support
- **Configuration**: Set environment variables to enable lazy loading
  ```bash
  export SMARTRECOVER_LAZY_LOADING=true
  export SMARTRECOVER_BATCH_SIZE=50
  ```
- **Benefits**:
  - Memory-efficient for large datasets
  - On-demand data loading
  - Pagination support

### 3. Unique ID Management
- **Guarantee**: All IDs are unique across all datasets
- **Format**: 
  - Incidents: `INC001`, `INC002`, ...
  - Tickets: `SNOW001`, `JIRA-001`, ...
  - Docs: `CONF001`, `CONF002`, ...
  - Changes: `CHG001`, `CHG002`, ...

### 4. Preserve Original Data
- **Flag**: `--preserve-existing`
- **Purpose**: Maintain test compatibility by preserving original data
- **Behavior**: Loads existing data and appends new data without overwriting

## Command-Line Options

```
usage: generate_mock_data.py [-h] [--scale SCALE] [--incidents INCIDENTS] 
                             [--validate] [--seed SEED] [--output-dir OUTPUT_DIR]
                             [--preserve-existing]

Options:
  --scale SCALE            Scale factor (e.g., 10 for 10x current 15 incidents)
  --incidents INCIDENTS    Explicit number of incidents to generate
  --validate              Validate generated data before saving
  --seed SEED             Random seed for reproducibility (default: 42)
  --output-dir OUTPUT_DIR Output directory for CSV files
  --preserve-existing     Preserve existing data and only append new data
```

## Examples

### Example 1: Expand Data by 10x (Preserving Original)
```bash
python backend/data/generate_mock_data.py --scale 10 --preserve-existing
```
**Result**: Original 15 incidents + 135 new = 150 total

### Example 2: Generate Fresh Dataset
```bash
python backend/data/generate_mock_data.py --incidents 100 --seed 123
```
**Result**: 100 brand new incidents with seed 123

### Example 3: Validate Data Quality
```bash
python backend/data/generate_mock_data.py --scale 5 --validate
```
**Result**: Generates 75 incidents and validates all relationships

### Example 4: Generate to Custom Directory
```bash
python backend/data/generate_mock_data.py --scale 2 --output-dir /tmp/test_data
```
**Result**: Generates data to `/tmp/test_data` without affecting production data

## Lazy Loading API

The mock_data module supports lazy loading for large datasets:

### Paginated Loading
```python
from backend.data import mock_data

# Load first page of 50 incidents
page1 = mock_data.load_incidents_paginated(page=1, page_size=50)
print(f"Total: {page1['total']}, Has more: {page1['has_more']}")
```

### Iterator Pattern
```python
from backend.data import mock_data

# Process incidents one at a time (memory efficient)
for incident in mock_data.iter_incidents():
    process_incident(incident)
```

### Batch Loading
```python
from backend.data import mock_data

# Process in batches
for batch in mock_data._load_incidents_lazy(batch_size=100):
    process_batch(batch)
```

## Data Templates

The generator uses realistic templates for:
- **Incident Titles**: 20+ patterns (database timeouts, API latency, etc.)
- **Services**: 28 different service types
- **Severities**: low, medium, high, critical
- **Teams**: 11 different team types
- **Ticket Resolutions**: 10+ detailed resolution patterns
- **Change Descriptions**: 28+ change types

## Validation

The generator validates:
- ✅ Unique IDs across all datasets
- ✅ Incident references exist
- ✅ Ticket types are consistent
- ✅ Similar incidents have resolutions
- ✅ Related changes have descriptions

## Data Statistics

After generating with `--scale 10`:
- **Incidents**: 150 (15 original + 135 new)
- **Tickets**: ~290 (1-3 per incident)
- **Docs**: ~230 (1-2 per incident)
- **Changes**: ~230 (1-2 per incident)

## Environment Variables

Configure lazy loading behavior:
```bash
# Enable lazy loading
export SMARTRECOVER_LAZY_LOADING=true

# Set batch size for lazy loading
export SMARTRECOVER_BATCH_SIZE=50
```

## Files Generated

- `incidents.csv` - Core incident data
- `servicenow_tickets.csv` - ServiceNow/Jira tickets
- `confluence_docs.csv` - Documentation references
- `change_correlations.csv` - Recent change deployments

## Testing

Run tests to ensure data integrity:
```bash
# Test all mock data functionality
pytest backend/tests/test_mock_data.py -v

# Test specific functionality
pytest backend/tests/test_mock_data.py::TestMockDataLoading -v
```

## Best Practices

1. **Always use --preserve-existing** when expanding production data
2. **Use --validate** to catch data quality issues early
3. **Set --seed** for reproducible test data
4. **Use lazy loading** for datasets > 100 incidents
5. **Test after generation** to ensure compatibility

## Troubleshooting

### Issue: Validation fails
**Solution**: Check that original data doesn't have validation issues. Skip validation if issues are in original data.

### Issue: IDs collide
**Solution**: Use `--preserve-existing` flag to track existing IDs.

### Issue: Out of memory
**Solution**: Enable lazy loading with `SMARTRECOVER_LAZY_LOADING=true`.

## Future Enhancements

Potential improvements:
- Support for other data sources (Jira, GitHub Issues)
- ML-based realistic data generation
- Time-series incident patterns
- Custom template injection
- Multi-language support
