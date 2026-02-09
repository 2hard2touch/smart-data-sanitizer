# Smart Data Sanitizer MVP

A command-line tool that automatically detects and replaces Personally Identifiable Information (PII) in JSON datasets with semantically valid fake data while maintaining referential integrity.

## Overview

The Smart Data Sanitizer helps developers sanitize production data for testing, development, or sharing purposes without compromising data utility or consistency. It detects common PII types (emails, phone numbers, names, credit card numbers) and replaces them with realistic fake data while ensuring that identical values are consistently replaced throughout the dataset.

### Goals

- **Privacy Protection**: Remove sensitive personal information from datasets to comply with privacy regulations
- **Data Utility**: Maintain data structure, relationships, and format so sanitized data remains useful for testing
- **Consistency**: Ensure referential integrity by mapping identical inputs to identical outputs
- **Simplicity**: Provide a straightforward CLI tool that requires no configuration or API keys
- **Extensibility**: Support future enhancements like LLM-based detection without architectural changes


## Installation

This project uses `uv` for dependency management. To set up the development environment:

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix/macOS:
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"
```

## Usage

The Smart Data Sanitizer can be used in two ways:
1. **Web Interface** (Streamlit) - User-friendly graphical interface for uploading and sanitizing files
2. **Command Line** (CLI) - Direct command-line tool for automation and scripting

### Web Interface (Streamlit)

The web interface provides an intuitive graphical way to sanitize JSON files without using the command line.

**Starting the Web Interface:**

**Windows:**
```cmd
.venv\Scripts\python.exe -m streamlit run src/data_sanitizer/streamlit_app.py
```

**Unix/macOS:**
```bash
.venv/bin/python -m streamlit run src/data_sanitizer/streamlit_app.py
```

The application will open in your default web browser at `http://localhost:8501`.

**Using the Web Interface:**

1. **Upload JSON File**: Click "Browse files" and select your JSON file containing PII
2. **Configure Output**: Enter a filename for the sanitized output (e.g., "sanitized_output.json")
3. **Sanitize**: Click the "Sanitize" button to process the file
4. **View Results**: See summary statistics including:
   - Records processed
   - PII fields detected
   - PII replacements made
   - Output file path
5. **Download**: Click "Download Sanitized File" to save the sanitized JSON

**Prerequisites:**
- Streamlit is included in the project dependencies and installed automatically with `uv pip install -e ".[dev]"`
- A modern web browser (Chrome, Firefox, Safari, Edge)
- The web interface uses the same sanitization logic as the CLI, ensuring consistent results

**Benefits of the Web Interface:**
- No command-line knowledge required
- Visual feedback and progress indicators
- Easy file upload and download
- Clear error messages and validation
- Perfect for one-off sanitization tasks

### Command Format

**CLI Usage:**

```
# Windows
.venv\Scripts\python.exe -m data_sanitizer.cli <input_file> <output_file> [--verbose]

# Unix/macOS
.venv/bin/python -m data_sanitizer.cli <input_file> <output_file> [--verbose]
```

**Arguments:**
- `input_file` - Path to your JSON file containing PII (required)
- `output_file` - Path where sanitized JSON will be written (required)
- `--verbose` - Optional flag for detailed logging output

**Note:** The tool must be run using the virtual environment's Python interpreter directly. Standard activation scripts may not work in all environments.


### Quick Start

**Windows:**
```cmd
# Navigate to project directory
cd path\to\data_sanitizer

# Run the sanitizer
.venv\Scripts\python.exe -m data_sanitizer.cli input.json output.json

# Or start the web interface
.venv\Scripts\python.exe -m streamlit run src/data_sanitizer/streamlit_app.py
```

**Unix/macOS:**
```bash
# Navigate to project directory
cd /path/to/data_sanitizer

# Run the sanitizer
.venv/bin/python -m data_sanitizer.cli input.json output.json

# Or start the web interface
.venv/bin/python -m streamlit run src/data_sanitizer/streamlit_app.py
```

## Example

### Try It Yourself with Sample Data

The project includes sample datasets you can use to test the sanitizer:

**Windows:**
```cmd
.venv\Scripts\python.exe -m data_sanitizer.cli tests/fixtures/sample_dirty_data.json my_output.json
```

**Unix/macOS:**
```bash
.venv/bin/python -m data_sanitizer.cli tests/fixtures/sample_dirty_data.json my_output.json
```
### Basic Example

**Input** (`dirty_data.json`):
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "status": "active"
  }
]
```
**Output** (`clean_data.json`):
```json
[
  {
    "id": 1,
    "name": "Michael Thompson",
    "email": "michael.thompson@example.org",
    "phone": "+1-555-234-5678",
    "status": "active"
  }
]
```

**Summary**:
```
Sanitization completed successfully!

Summary:
  Records processed: 1
  PII fields detected: 3
  PII replacements made: 3

Sanitized data written to: clean_data.json
```

### Advanced Example with Nested Data

**Input**:
```json
[
  {
    "user_id": 42,
    "first_name": "Jane",
    "last_name": "Smith",
    "contact": {
      "email": "jane.smith@company.com",
      "phone": "(555) 987-6543"
    },
    "payment": {
      "card": "4532-1234-5678-9010",
      "billing_name": "Jane Smith"
    },
    "notes": "Contact Jane Smith at jane.smith@company.com for urgent matters."
  }
]
```

**Output**:
```json
[
  {
    "user_id": 42,
    "first_name": "Sarah",
    "last_name": "Martinez",
    "contact": {
      "email": "sarah.martinez@company.org",
      "phone": "(555) 345-6789"
    },
    "payment": {
      "card": "4532-9876-5432-1098",
      "billing_name": "Sarah Martinez"
    },
    "notes": "Contact Sarah Martinez at sarah.martinez@company.org for urgent matters."
  }
]
```

**Key Features Demonstrated**:
- **Referential Integrity**: "Jane Smith" and "jane.smith@company.com" are consistently replaced throughout
- **Cross-Field Consistency**: First name "Jane" and last name "Smith" map to the same fake person ("Sarah Martinez")
- **Nested Structure Preservation**: JSON structure remains intact
- **Format Preservation**: Phone format "(555) 987-6543" is maintained
- **Non-PII Preservation**: user_id remains unchanged

## Architecture

The sanitizer follows a modular, plugin-based architecture:

- **CLI Module**: Command-line interface and user interaction
- **Sanitizer Orchestrator**: Coordinates detection and replacement
- **Detector Plugins**: Modular PII detection strategies (email, phone, name, credit card)
- **Replacer**: Generates consistent fake data using Faker library
- **Consistency Cache**: Maintains mapping between original and fake values

### Architectural Decisions

**Why Presidio + Regex for Detection?**

We use a hybrid approach combining regex patterns and Microsoft's Presidio library:
- **Regex patterns** provide fast, deterministic detection for structured data (emails, phone numbers, credit card numbers)
- **Presidio** offers robust, pre-trained entity recognition for names without requiring API keys or external services
- This combination provides excellent coverage for common PII types while maintaining performance and reliability

**Why Faker for Generation?**

Faker is the industry-standard library for generating realistic fake data:
- Supports all required PII types (names, emails, phone numbers, credit card numbers)
- Generates semantically valid data that passes format validation (e.g., Luhn algorithm for credit cards)
- Deterministic when seeded, enabling reproducible tests and consistent behavior
- Well-maintained with extensive documentation and community support

**Why Plugin Architecture?**

The detector system uses a plugin-based design for extensibility:
- Each detector is independent and can be developed/tested in isolation
- New detection strategies (including future LLM integration) can be added without modifying core logic
- Detectors can be easily enabled/disabled via configuration
- Supports different detection approaches (regex, ML models, API-based) through a common interface

**Why In-Memory Consistency Cache?**

The MVP uses a simple dictionary-based cache for maintaining referential integrity:
- Sufficient for typical datasets that fit in memory
- Provides O(1) lookup performance for consistency checks
- Simple implementation reduces complexity and potential bugs
- Can be extended to persistent storage (Redis, database) if needed for larger datasets in future versions

## Development

### Running the Tool

**Windows:**
```cmd
.venv\Scripts\python.exe -m data_sanitizer.cli input.json output.json
```

**Unix/macOS:**
```bash
.venv/bin/python -m data_sanitizer.cli input.json output.json
```

### Code Quality

**Linting:**
```cmd
# Windows
.venv\Scripts\python.exe -m ruff check src/ tests/

# Unix/macOS
.venv/bin/python -m ruff check src/ tests/
```

**Formatting:**
```cmd
# Windows
.venv\Scripts\python.exe -m ruff format src/ tests/

# Unix/macOS
.venv/bin/python -m ruff format src/ tests/
```

## Testing

The project includes comprehensive testing with a dual approach:

- **Unit Tests** (177 tests): Test individual components, specific examples, and edge cases
- **Property-Based Tests** (53 tests): Verify universal correctness properties using Hypothesis (100+ iterations per property)
- **Integration Tests** (21 tests): Validate end-to-end workflows with realistic data

**Total: 251 tests with 95% code coverage**

### Test Categories

**Unit Tests** (`tests/unit/`):
- Detector tests: Email, phone, name, and credit card detection with various formats
- Replacer tests: Fake data generation, consistency, and format preservation
- Sanitizer tests: File I/O, JSON parsing, structure preservation
- CLI tests: Argument parsing, error handling, exit codes
- Streamlit tests: Web interface components and workflows
- Model tests: Data structures and validation

**Property-Based Tests** (`tests/property/`):
- Consistency properties: Same input → same output across all PII types
- Validity properties: Generated data matches expected formats
- Preservation properties: Structure, format, and case preservation
- Detection properties: Field-name-agnostic PII detection
- CLI properties: Exit codes, error handling, summary display

**Integration Tests** (`tests/integration/`):
- Full sanitization workflows with sample datasets
- Edge cases: Empty data, nested structures, mixed PII
- Error handling: File not found, invalid JSON, permission errors
- Consistency across multiple runs with same seed
- Output validation and re-sanitization

### Running Tests

Run the complete test suite:

**Windows:**
```cmd
# Run all tests (251 tests, ~2.5 minutes)
.venv\Scripts\python.exe -m pytest

# Run with coverage report
.venv\Scripts\python.exe -m pytest --cov=src/data_sanitizer --cov-report=html

# Run specific test categories
.venv\Scripts\python.exe -m pytest tests/unit/          # Unit tests
.venv\Scripts\python.exe -m pytest tests/property/      # Property-based tests
.venv\Scripts\python.exe -m pytest tests/integration/   # Integration tests

# Run with verbose output
.venv\Scripts\python.exe -m pytest -v
```

**Unix/macOS:**
```bash
# Run all tests
.venv/bin/python -m pytest

# Run with coverage report
.venv/bin/python -m pytest --cov=src/data_sanitizer --cov-report=html

# Run specific test categories
.venv/bin/python -m pytest tests/unit/
.venv/bin/python -m pytest tests/property/
.venv/bin/python -m pytest tests/integration/

# Run with verbose output
.venv/bin/python -m pytest -v
```

### Test Coverage

The test suite achieves **95% code coverage** across all modules:

| Module | Coverage |
|--------|----------|
| models.py | 100% |
| exceptions.py | 100% |
| email_detector.py | 100% |
| name_detector.py | 100% |
| replacer.py | 99% |
| phone_detector.py | 97% |
| cli.py | 96% |
| credit_card_detector.py | 94% |
| sanitizer.py | 88% |
| base.py | 83% |

**View detailed coverage report:**
```cmd
# Windows
.venv\Scripts\python.exe -m pytest --cov=src/data_sanitizer --cov-report=html
start htmlcov\index.html

# Unix/macOS
.venv/bin/python -m pytest --cov=src/data_sanitizer --cov-report=html
open htmlcov/index.html
```

### Property-Based Testing

The project uses Hypothesis for property-based testing, which validates correctness properties across randomly generated inputs:

**21 Correctness Properties Validated:**
1. JSON Round-Trip Validity
2. Invalid JSON Error Handling
3. Structure and Non-PII Preservation
4. Field-Name-Agnostic PII Detection
5. Email Replacement Validity
6. Email Consistency
7. Phone Replacement Validity
8. Phone Consistency
9. Phone Format Preservation
10. Name Type Preservation
11. Name Consistency
12. Name Case Preservation
13. Cross-Field Name Consistency
14. Credit Card Replacement Validity
15. Credit Card Consistency
16. Replacement Uniqueness
17. CLI Missing Arguments Error
18. CLI Exit Code Correctness
19. CLI Summary Display
20. JSON Parse Error Details
21. Detector Configuration

Each property test runs 100+ iterations with randomly generated data to ensure correctness across a wide input space.

### Sample Test Data

The project includes test fixtures in `tests/fixtures/`:
- `sample_dirty_data.json`: Realistic dataset with various PII types
- `edge_cases.json`: Edge cases (empty arrays, nested structures, mixed PII)
- `invalid_json.txt`: Malformed JSON for error testing

You can use these files to manually test the sanitizer or as examples for creating your own test data.

## Requirements

- Python 3.11+
- Operating System: Windows, macOS, or Linux
- Dependencies: faker, presidio-analyzer, presidio-anonymizer
- Dev dependencies: pytest, pytest-cov, hypothesis, ruff

**Note:** The tool works completely offline and does not require any API keys or external services.

## Troubleshooting

### Common Issues

**"The system cannot find the path specified" (Windows)**

Make sure you're in the project directory first.

**"python.exe is not recognized"**

Use the full path to the virtual environment's Python: `.venv\Scripts\python.exe` (Windows) or `.venv/bin/python` (Unix/macOS).

**"No such file or directory" for input file**

Check that your input file path is correct. Use `dir` (Windows) or `ls` (Unix/macOS) to list files.

**"Invalid JSON" error**

Ensure your input file contains a valid JSON array: `[{...}, {...}]`. The tool expects an array of objects.

**Tests fail with "ModuleNotFoundError"**

Install dependencies: `uv pip install -e ".[dev]"`

**Permission denied when writing output**

Check write permissions for the output directory, or specify a different output path.

### Getting Help

If you encounter other issues:

1. Verify dependencies are installed: `uv pip install -e ".[dev]"`
2. Check Python version: `.venv\Scripts\python.exe --version` (should be 3.11+)
3. Run the test suite: `.venv\Scripts\python.exe -m pytest`
4. Review error messages carefully for specific details

## License

MIT

## Future Enhancements

The following features are planned for future versions:

- **LLM-based Detection**: Integrate large language models for context-aware PII detection that can identify sensitive information based on semantic understanding
- **Streaming Support**: Process large files without loading entirely into memory, enabling sanitization of multi-gigabyte datasets
- **CSV Support**: Add CSV input/output format support for broader data format compatibility
- **Custom PII Types**: Allow users to define custom PII patterns and detection rules specific to their domain
- **Performance Optimization**: Implement parallel processing for large datasets to improve throughput
- **Multiple Anonymization Strategies**: Support different approaches beyond replacement (masking, hashing, tokenization, etc.)
- **Configuration Files**: Support YAML/TOML configuration files for detector settings and customization
- **Multilingual Support**: Detect PII in non-English text and international formats

## Limitations (MVP Scope)

This MVP version has the following limitations:

- **In-Memory Processing**: Entire dataset must fit in memory; not suitable for extremely large files (>1GB)
- **JSON Only**: Currently supports only JSON format; CSV, XML, and other formats not supported
- **English-Centric**: Detection optimized for English text and US/international formats
- **Limited PII Types**: Detects only emails, phone numbers, names, and credit card numbers; other PII types (SSN, passport numbers, etc.) not included
- **No Streaming**: Files are processed in full before writing output
- **Basic Name Detection**: May miss names in certain contexts or with unusual formatting
- **No Custom Rules**: Users cannot define custom PII patterns without modifying code

These limitations are intentional for the MVP and will be addressed in future releases based on user feedback and requirements.
