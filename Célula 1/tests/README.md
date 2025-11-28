# Tests

This directory contains unit tests and property-based tests.

## Structure

- `unit/` - Unit tests for Lambda functions and business logic
- `property/` - Property-based tests using Hypothesis
- `integration/` - Integration tests (optional)

## Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run property tests only
pytest tests/property/

# Run with coverage
pytest --cov=src --cov-report=html
```
