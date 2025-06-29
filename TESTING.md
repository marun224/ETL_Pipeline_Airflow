# Testing Guide for ETL Pipeline

This document provides comprehensive information about testing the ETL Pipeline project, including test structure, execution, and best practices.

## 📋 Table of Contents

- [Test Structure](#test-structure)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## 🏗️ Test Structure

```
tests/
├── __init__.py
├── fixtures/
│   ├── sample_data.py      # Sample data for testing
│   └── sample_html.py      # Sample HTML responses
├── unit/
│   ├── __init__.py
│   ├── test_amazon_scraper.py      # Tests for AmazonBookScraper
│   ├── test_data_processor.py      # Tests for BookDataProcessor
│   ├── test_database_manager.py    # Tests for DatabaseManager
│   └── test_etl_functions.py       # Tests for ETL integration functions
└── integration/
    ├── __init__.py
    ├── test_dag_structure.py       # DAG structure and configuration tests
    └── test_end_to_end.py          # End-to-end pipeline tests
```

## 🧪 Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation:

- **AmazonBookScraper**: Web scraping functionality
- **BookDataProcessor**: Data validation and transformation
- **DatabaseManager**: Database operations
- **ETL Functions**: Integration functions for Airflow

### Integration Tests

Integration tests verify component interactions:

- **DAG Structure**: Airflow DAG configuration and task dependencies
- **End-to-End**: Complete pipeline execution flow

## 🚀 Running Tests

### Prerequisites

Install testing dependencies:

```bash
pip install -r requirements.txt
```

### Quick Start

Run all tests:

```bash
python run_tests.py
```

### Specific Test Categories

Run only unit tests:

```bash
python run_tests.py --unit
```

Run only integration tests:

```bash
python run_tests.py --integration
```

### Using pytest directly

Run all tests with pytest:

```bash
pytest tests/
```

Run specific test file:

```bash
pytest tests/unit/test_amazon_scraper.py
```

Run tests with coverage:

```bash
pytest --cov=dags tests/
```

### Verbosity Options

Quiet mode (minimal output):

```bash
python run_tests.py --quiet
```

Verbose mode (detailed output):

```bash
python run_tests.py --verbose
```

## 📊 Test Coverage

### Generating Coverage Reports

Generate HTML coverage report:

```bash
pytest --cov=dags --cov-report=html tests/
```

Generate terminal coverage report:

```bash
pytest --cov=dags --cov-report=term-missing tests/
```

### Coverage Targets

- **Unit Tests**: Aim for >90% code coverage
- **Integration Tests**: Focus on critical path coverage
- **Overall**: Target >85% total coverage

### Viewing Coverage

After generating HTML report:

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## ✍️ Writing Tests

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Unit Test

```python
import unittest
from unittest.mock import Mock, patch
from etl_functions import AmazonBookScraper

class TestAmazonBookScraper(unittest.TestCase):
    def setUp(self):
        self.scraper = AmazonBookScraper()
    
    @patch('etl_functions.requests.get')
    def test_fetch_page_success(self, mock_get):
        # Mock setup
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test execution
        result = self.scraper.fetch_page_content(1)
        
        # Assertions
        self.assertIsNotNone(result)
        mock_get.assert_called_once()
```

### Mocking Guidelines

1. **Mock External Dependencies**: HTTP requests, database connections
2. **Use Fixtures**: Reusable test data in `tests/fixtures/`
3. **Isolate Tests**: Each test should be independent
4. **Test Edge Cases**: Error conditions, empty data, malformed input

### Test Data Management

Use fixtures for consistent test data:

```python
from tests.fixtures.sample_data import SAMPLE_BOOK_DATA

def test_data_processing(self):
    result = process_books(SAMPLE_BOOK_DATA)
    self.assertEqual(len(result), 3)
```

## 🔄 Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python run_tests.py
    - name: Generate coverage
      run: pytest --cov=dags --cov-report=xml tests/
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

### Pre-commit Hooks

Set up pre-commit hooks to run tests automatically:

```bash
pip install pre-commit
pre-commit install
```

## 🛠️ Troubleshooting

### Common Issues

#### Import Errors

**Problem**: `ModuleNotFoundError` when running tests

**Solution**: Ensure Python path includes the dags directory:

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../dags'))
```

#### Mock Issues

**Problem**: Mocks not working as expected

**Solution**: Verify the import path in the patch decorator:

```python
# Correct: patch where the function is used
@patch('etl_functions.requests.get')

# Incorrect: patch where the function is defined
@patch('requests.get')
```

#### Airflow Dependencies

**Problem**: Airflow imports failing in tests

**Solution**: Mock Airflow components or install Airflow in test environment:

```python
from unittest.mock import Mock
import sys
sys.modules['airflow'] = Mock()
sys.modules['airflow.models'] = Mock()
```

### Test Environment Setup

For local development:

```bash
# Create virtual environment
python -m venv test_env
source test_env/bin/activate  # Linux/macOS
# test_env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
python run_tests.py
```

### Debugging Tests

Run specific test with debugging:

```bash
python -m pytest tests/unit/test_amazon_scraper.py::TestAmazonBookScraper::test_fetch_page_success -v -s
```

Use Python debugger in tests:

```python
import pdb; pdb.set_trace()
```

## 📈 Test Metrics

### Key Metrics to Track

1. **Test Coverage**: Percentage of code covered by tests
2. **Test Execution Time**: How long tests take to run
3. **Test Reliability**: Frequency of flaky tests
4. **Bug Detection Rate**: Tests catching real issues

### Performance Benchmarks

- Unit tests should run in <5 seconds
- Integration tests should run in <30 seconds
- Full test suite should run in <60 seconds

## 🎯 Best Practices

### Test Design

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: Focus on single behavior
3. **Descriptive Names**: Test names should explain what they test
4. **Independent Tests**: No dependencies between tests

### Data Management

1. **Use Fixtures**: Consistent, reusable test data
2. **Clean State**: Reset state between tests
3. **Realistic Data**: Test data should mirror production data
4. **Edge Cases**: Test boundary conditions

### Maintenance

1. **Regular Updates**: Keep tests updated with code changes
2. **Refactor Tests**: Apply same quality standards as production code
3. **Remove Obsolete Tests**: Delete tests for removed functionality
4. **Document Complex Tests**: Add comments for complex test logic

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Airflow Testing Guide](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html#testing)
- [Python Testing Best Practices](https://realpython.com/python-testing/)

---

For questions or issues with testing, please refer to the project documentation or open an issue in the repository.