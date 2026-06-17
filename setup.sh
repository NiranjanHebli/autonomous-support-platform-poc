#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Starting Project Environment Setup ==="

# 1. Create Python virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "Virtual environment (.venv) already exists."
fi

# 2. Activate virtual environment and install requirements
echo "Activating virtual environment and installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Setup Git hooks
echo "Setting up Git hooks..."
mkdir -p .git/hooks

# Copy hooks from tracked githooks/ directory to .git/hooks/
cp githooks/pre-commit .git/hooks/pre-commit
cp githooks/commit-msg .git/hooks/commit-msg

# Make hooks executable
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
echo "Git hooks configured successfully."

# 4. Generate dataset if it does not exist
if [ ! -d "data/policies" ] || [ -z "$(ls -A data/policies 2>/dev/null)" ]; then
    echo "Dataset policies folder is empty or does not exist."
    echo "Running dataset generation script..."
    python3 scripts/process_hf_dataset.py
else
    echo "Dataset policies already exist."
fi

echo "=== Setup Completed Successfully! ==="
