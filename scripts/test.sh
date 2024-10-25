#!/bin/bash
echo "Running tests..."

# Activate virtual environment
source venv/bin/activate

# Run tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=term-missing

echo "Tests complete!"
