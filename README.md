# Smart Data Sanitizer MVP

Tool that automatically detects and replaces Personally Identifiable Information (PII) in JSON datasets with semantically valid fake data while maintaining referential integrity.

Use the streamlit cloud demo at https://smart-data-sanitizer.streamlit.app/

## Overview

The Smart Data Sanitizer helps sanitize production data for testing, development, or sharing purposes without compromising data utility or consistency. It detects common PII types (emails, phone numbers, names, credit card numbers) and replaces them with realistic fake data while ensuring that identical values are consistently replaced throughout the dataset.

### Goals

- **Privacy Protection**: Remove sensitive personal information from datasets to comply with privacy regulations
- **Data Utility**: Maintain data structure, relationships, and format so sanitized data remains useful for testing
- **Consistency**: Ensure referential integrity by mapping identical inputs to identical outputs
- **Simplicity**: Provide a straightforward tool that requires no configuration or API keys
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
## Testing

The project includes comprehensive testing with a dual approach:

- **Unit Tests** (177 tests): Test individual components, specific examples, and edge cases
- **Property-Based Tests** (53 tests): Verify universal correctness properties using Hypothesis (100+ iterations per property)
- **Integration Tests** (21 tests): Validate end-to-end workflows with realistic data

**Total: 251 tests with 95% code coverage**


### Running Tests

Run the complete test suite:

**Windows:**
```cmd
# Run all tests (251 tests, ~2.5 minutes)
.venv\Scripts\python.exe -m pytest
```

**Unix/macOS:**
```bash
# Run all tests
.venv/bin/python -m pytest
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

### Sample Test Data

The project includes test fixtures in `tests/fixtures/`:
- `sample_dirty_data.json`: Realistic dataset with various PII types
- `edge_cases.json`: Edge cases (empty arrays, nested structures, mixed PII)
- `invalid_json.txt`: Malformed JSON for error testing

You can use these files to manually test the sanitizer or as examples for creating your own test data.

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

## License

MIT

## Заметка о приоритизации (Note on Prioritization)

### От каких фичей отказались намеренно?

Для соблюдения сроков разработки MVP были намеренно исключены следующие функции:

1. **LLM-интеграция для контекстного определения PII и генерации текста необходимой тональности**
   - Причина: Требует API-ключей, увеличивает сложность и стоимость использования
   - Решение: Использование Presidio (NLP-библиотека) для базового определения

2. **Потоковая обработка больших файлов**
   - Причина: Значительно усложняет архитектуру, требует управления памятью
   - Решение: Введение ограничения на размер файлов до 1GB (загрузка в память)

3. **Поддержка CSV, XML и других форматов**
   - Причина: Каждый формат требует отдельной логики парсинга и валидации
   - Решение: Использование формата JSON как наиболее распространенного формата для API

4. **Пользовательские правила определения PII**
   - Причина: Требует UI для конфигурации, валидации regex, документации
   - Решение: Предоставление фиксированного набора детекторов на первом этапе (электронная почта, номер телефона, ФИО, данные кредитной карты)

### Какие «углы срезали» в архитектуре?

1. **Упрощенная система детекторов**
  В инструменте используется упрощенная система детекторов пользовательских данных, которая не распознает 100% PII.

2. **Базовая консистентность замен**
    Кеш замен хранится только в памяти, поэтому разные итерации с одними исходными данными генерируют разные замены. В будущем возможно добавить сохранение mapping словаря в файл как опцию инструмента

3. **Отсутствие валидации выходных данных**
    В результирующих данных замененный email может не соответствовать домену компании. Лечится валидаторами и введением правил для генерации данных

4. **Отсутствие метрик и логирования**
    В процессе выполнения логируются только критические события, поэтому сложно производить отладку. В будущем необходимо ввести структурированное логирование и мониторинг метрик производительности.
  
5. **Поддержка только английского языка PII**
    Для упрощения детекции существующими бибилотеками, инструмент корректно работает с PII на английском языке.

### Как бы развивали инструмент дальше?
  В целом улучшения инструмента можно разделить на несколько групп по актуальности и срочности реализации.

#### Срочные и актуальные

1. **Streaming для больших файлов**
   Поддержать обработку файлов по частям и поддержку больших файлов. Ввести прогресс-бар для длительных операций

2. **Поддержка CSV формата**
   Поддержать исходные данные в CSV формате с сохранением структуры, автоопределнием разделителей и кодировки и обработкой заголовков.

3. **Поддержка других языков**
   Подержать работу с PII представленной на разных языках.

#### Улучшения средней срочности

1. **LLM-интеграция (опциональная)**
   Интегрировать LLM для определения PII и для замены семантической текстовой информации

2. **Расширенные типы PII**
   Поддержать более широкий пул типов персональной информации (номер паспорта, страховки, IP-адрес, Биометрические данные, данные местоположения)

3. **Web API и Docker**
   Собрать DOCKER-образ для развертывания

#### Долгосрочные улучшения (6-12 месяцев):

1. **Производительность**
   Увеличение производительности за счет параллельной обработки, кеширования и оптимизации.

2. **Расширенная экосистема**
   Интеграция с популярными типами БД, библиотека для Python