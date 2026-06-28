# Cartly Support Copilot - Runtime View

This document contains the Runtime View diagram, illustrating the dynamic sequence of interactions between the user, the messaging bridge, and the internal components during ticket processing.

```mermaid
sequenceDiagram
    participant Cust as Customer
    participant MB as Messaging Bridge
    participant API as FastAPI Backend
    participant Class as Classifier (LightGBM)
    participant RAG as RAG Pipeline
    participant DB as Vector Store (ChromaDB)
    participant LLM as Local LLM (Ollama)
    participant Agent as Support Agent

    Cust->>MB: Sends support message
    MB->>API: Ingests raw text
    API->>Class: Classify Intent
    Class-->>API: Returns Intent & Confidence
    API->>RAG: Trigger Document Retrieval
    RAG->>DB: Semantic Search (all-MiniLM-L6-v2)
    DB-->>RAG: Returns Top-k Policy Chunks
    RAG->>LLM: Generate Draft (Prompt + Context)
    LLM-->>RAG: Returns Draft Response
    RAG->>LLM: Groundedness Check (Quality Critic)
    LLM-->>RAG: Pass/Fail Evaluation
    RAG-->>API: Returns Approved Draft
    API->>Agent: Present "Pending Approval" Draft in UI
    Agent->>MB: Approves & Sends Reply
    MB->>Cust: Delivers Message
```
