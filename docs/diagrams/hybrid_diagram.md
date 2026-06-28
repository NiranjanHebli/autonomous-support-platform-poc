# Cartly Support Copilot - Hybrid Architecture Diagram

This document contains a Hybrid diagram, combining structural components with high-level data and control flow to provide a comprehensive architectural overview.

```mermaid
flowchart LR
    classDef person fill:#08427b,color:#fff,stroke:#052e56,stroke-width:2px,rx:8px,ry:8px
    classDef container fill:#1168bd,color:#fff,stroke:#0b4884,stroke-width:2px,rx:8px,ry:8px
    classDef external fill:#999999,color:#fff,stroke:#6b6b6b,stroke-width:2px,rx:8px,ry:8px
    classDef db fill:#08427b,color:#fff,stroke:#052e56,stroke-width:2px,rx:8px,ry:8px

    Cust["Customer"]:::person
    MB["Messaging Bridge"]:::external
    Agent["Support Agent"]:::person
    
    subgraph Copilot["Cartly Support Copilot (Local Server)"]
        direction TB
        ClassApp["LightGBM Intent Classifier"]:::container
        FastAPI["FastAPI Orchestrator"]:::container
        
        subgraph RAG["RAG Pipeline"]
            PII["PII Masker"]:::container
            Retriever["Vector Retriever"]:::container
            Critic["Quality Critic"]:::container
        end
        
        subgraph Inference["Local Inference Engines"]
            Embed["Sentence Transformers"]:::container
            LLM["Ollama (llama3.1:8b)"]:::container
        end
        
        DB[("ChromaDB Vector Store")]:::db
    end
    
    Cust -- 1. Social Message --> MB
    MB -- 2. Ingest Payload --> FastAPI
    FastAPI -- 3. Classify --> ClassApp
    FastAPI -- 4. Mask Data --> PII
    FastAPI -- 5. Query --> Retriever
    Retriever -- 6. Encode Query --> Embed
    Retriever -- 7. Semantic Search --> DB
    FastAPI -- 8. Generate Draft --> LLM
    FastAPI -- 9. Validate Draft --> Critic
    Critic -.-> LLM
    FastAPI -- 10. Present Draft --> Agent
    Agent -- 11. Approve/Send --> MB
```
