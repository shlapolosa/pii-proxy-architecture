#!/bin/bash

# Installation script for PII Proxy Architecture Backend

set -e

echo "Installing PII Proxy Architecture Backend dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install main dependencies
echo "Installing main dependencies..."
pip install -r requirements.txt

# Install test dependencies
echo "Installing test dependencies..."
pip install -r test-requirements.txt

# Download spaCy language model
echo "Downloading spaCy language model..."
python -m spacy download en_core_web_lg

echo "Installation complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"