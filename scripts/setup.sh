#!/bin/bash
echo "Setting up development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install black flake8 pytest pre-commit

# Initialize pre-commit
pre-commit install

echo "Setup complete!"
