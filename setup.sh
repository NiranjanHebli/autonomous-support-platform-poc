#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "=== Starting Project Environment Setup ==="

# 1. Install dependencies using uv
echo "Installing dependencies with uv..."
uv sync

# 2. Setup Git hooks
echo "Setting up Git hooks..."
mkdir -p .git/hooks

# Copy hooks from tracked githooks/ directory to .git/hooks/
cp githooks/pre-commit .git/hooks/pre-commit
cp githooks/commit-msg .git/hooks/commit-msg

# Make hooks executable
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
echo "Git hooks configured successfully."

# 3. Generate dataset if it does not exist
if [ ! -d "data/policies" ] || [ -z "$(ls -A data/policies 2>/dev/null)" ]; then
    echo "Dataset policies folder is empty or does not exist."
    echo "Running dataset generation script..."
    uv run python scripts/process_hf_dataset.py
else
    echo "Dataset policies already exist."
fi

echo "=== Setup Completed Successfully! ==="
