# Autonomous Customer-Support Resolution Platform

## Goal of the Project
The goal of this project is to scope, design, and de-risk the **Cartly Support Copilot**, an agentic AI customer support system. 

Specifically, this project aims to:
- **Contract System Performance**: Define what "good" performance looks like in numbers (KPIs, success metrics) and draft a concrete Product Requirements Document (PRD) and Technical Design Document.
- **De-risk the Highest Assumption**: Prove that the hardest part of the system (retrieval of policy documents) is highly accurate by building a python retrieval spike using ChromaDB, comparing different chunking strategies, and establishing retrieval hit-rate metrics.

---

## Setup and Run

To set up the project environment completely, follow these steps:

### 1. Run the Setup Automation Script
This script creates the virtual environment, installs dependencies, sets up conventional commit and black formatting Git hooks, and generates the policy dataset:

```bash
# Make the setup script executable (only needed once)
chmod +x setup.sh

# Run the setup script
./setup.sh
```

### 2. Activate the Virtual Environment
After the setup script completes successfully, activate the virtual environment in your active terminal session before running any code:

```bash
source .venv/bin/activate
```

---

### Manual Steps (Alternative)
If you prefer to set up components manually:

#### 1. Environment Setup
```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### 2. Git Hooks Setup
```bash
# Copy and configure the hooks
cp githooks/pre-commit .git/hooks/pre-commit
cp githooks/commit-msg .git/hooks/commit-msg
chmod +x .git/hooks/pre-commit .git/hooks/commit-msg
```

#### 3. Data Corpus Generation
To fetch and generate the policy documents:
```bash
python3 scripts/process_hf_dataset.py
```
This will extract unique intents and save them as markdown documents in `/data/policies/`.
