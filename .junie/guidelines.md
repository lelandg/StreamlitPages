# StreamlitPages Development Guidelines

This document provides guidelines and instructions for developing and maintaining the StreamlitPages project.

## Build/Configuration Instructions

### Environment Setup

1. **Python Version**: This project requires Python 3.8 or higher.

2. **Virtual Environment**: Always use a virtual environment for development.
   ```powershell
   # Create a virtual environment
   python -m venv .venv
   
   # Activate the virtual environment
   .\.venv\Scripts\Activate
   ```

3. **Dependencies**: Install the required dependencies using pip.
   ```powershell
   pip install -r requirements.txt
   ```

### Running the Application

To run the Streamlit application:

```powershell
streamlit run app.py
```

This will start the Streamlit server and open the application in your default web browser.

## Testing Information

### Test Structure

- Tests are located in the `tests` directory
- Each module should have a corresponding test file named `test_<module_name>.py`
- Use pytest for running tests

### Running Tests

To run all tests:

```powershell
python -m pytest
```

To run tests with verbose output:

```powershell
python -m pytest -v
```

To run a specific test file:

```powershell
python -m pytest tests\test_utils.py
```

### Writing Tests

1. Create test functions with names starting with `test_`
2. Use descriptive function names that indicate what is being tested
3. Include docstrings that explain the purpose of the test
4. Use pytest's assertion methods for validation

Example:

```python
def test_format_number_integer():
    """Test formatting an integer."""
    assert format_number(1000) == "1,000.00"
```

## Code Style and Development Guidelines

### Code Style

- Follow PEP 8 style guidelines for Python code
- Use 4 spaces for indentation (not tabs)
- Maximum line length of 88 characters (compatible with Black formatter)
- Use docstrings for all public functions, classes, and methods

### Function Documentation

Document functions using the following format:

```python
def function_name(param1, param2):
    """
    Brief description of the function.
    
    Args:
        param1 (type): Description of param1
        param2 (type): Description of param2
        
    Returns:
        return_type: Description of the return value
    """
    # Function implementation
```

### Project Structure

- `app.py`: Main Streamlit application entry point
- `utils.py`: Utility functions used by the application
- `tests/`: Directory containing all test files
  - `test_utils.py`: Tests for utility functions
  - `__init__.py`: Makes the tests directory a Python package

### Development Workflow

1. Create a new branch for each feature or bug fix
2. Write tests before implementing new features (Test-Driven Development)
3. Run tests locally before pushing changes
4. Document any new functionality in code comments and docstrings