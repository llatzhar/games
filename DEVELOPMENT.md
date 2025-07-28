# Development Setup Guide

## Quick Start

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
# Windows (PowerShell)
.\test.ps1 test

# Linux/macOS
make test

# Or directly with Python
python -m unittest discover -s tests -p "test_*.py" -v
```

### 3. Check Code Quality
```bash
# Windows (PowerShell)
.\test.ps1 check

# Linux/macOS
make check
```

### 4. Run Game (if applicable)
```bash
python game.py
```

## CI/CD Status

- Tests run automatically on push to `main` and `develop` branches
- Code quality checks enforce consistent formatting
- Coverage reports uploaded to Codecov

## Available Commands

### Windows (PowerShell)
- `.\test.ps1 install` - Install dependencies
- `.\test.ps1 test` - Run tests
- `.\test.ps1 test-coverage` - Run tests with coverage
- `.\test.ps1 format` - Format code
- `.\test.ps1 lint` - Check code quality
- `.\test.ps1 clean` - Clean temporary files

### Linux/macOS (Make)
- `make install` - Install dependencies
- `make test` - Run tests
- `make test-coverage` - Run tests with coverage
- `make format` - Format code
- `make lint` - Check code quality
- `make clean` - Clean temporary files
