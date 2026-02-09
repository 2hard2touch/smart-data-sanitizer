# Running Tests

## ⚠️ IMPORTANT: Use the Correct Command

**To run tests in this project, use:**

```powershell
.venv\Scripts\python.exe -m pytest [path] [options]
```

## Examples

```powershell
# Run all tests
.venv\Scripts\python.exe -m pytest

# Run specific test file
.venv\Scripts\python.exe -m pytest tests/unit/test_models.py -v

# Run with coverage
.venv\Scripts\python.exe -m pytest --cov=src/data_sanitizer --cov-report=html
```

## ❌ Do NOT Use

- `pytest` (will fail - not in PATH)
- `.venv\Scripts\Activate.ps1 ; pytest` (will fail - execution policy)
- `python -m pytest` (will use wrong Python)

## Why?

This project uses a virtual environment at `.venv` on Windows. The PowerShell execution policy prevents script activation, so we must call the Python interpreter directly.

## More Info

See `.kiro/dev-notes.md` for all development commands.
