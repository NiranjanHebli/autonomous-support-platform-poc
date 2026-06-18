# Autonomous Support Platform POC

## Overview

This repository contains the Proof of Concept (POC) for the Autonomous Support Platform. The solution interfaces with the Matrix.org (Element) communications protocol to provide bidirectional messaging and data ingestion capabilities.

## Components

1. **Matrix Client CLI (`main.py`)**
   A command-line interface tool to interact directly with Matrix rooms.
   - List joined rooms and pending invites.
   - View recent messages, including automatic downloading of media attachments.
   - Send messages and reply directly to specific events.
   - Join new rooms by alias or ID.

2. **Databricks Ingestion Script (`databricks_ingest.py`)**
   A stateful ingestion script designed to extract messages for downstream processing (e.g., Databricks pipelines).
   - Syncs and tracks new messages using Matrix synchronization tokens.
   - Resolves message threads and recipient information for replies.
   - Generates structured JSON payloads of the extracted conversation data.

## Setup and Configuration

1. Create a `.env` file in the root directory with your credentials:
   ```env
   ACCESS_TOKEN="your_matrix_access_token_here"
   MATRIX_ROOM_ID="!your_room_id:matrix.org"
   ```

2. Install the necessary dependencies:
   ```bash
   uv sync
   ```
   *(or install from `pyproject.toml` via `pip`)*

3. Execute the applications:
   - **CLI Tool:** `python main.py --help`
   - **Data Ingestion:** `python databricks_ingest.py`
