# Cartly Support Copilot - C4 Context Diagram

This document contains the System Context diagram for the Cartly Support Copilot, describing the system's high-level interactions with users and external systems.

```mermaid
flowchart TD
    %% C4-like Styling without stereotypes (<<System>>, etc.)
    classDef person fill:#08427b,color:#fff,stroke:#052e56,stroke-width:2px,rx:8px,ry:8px
    classDef system fill:#1168bd,color:#fff,stroke:#0b4884,stroke-width:2px,rx:8px,ry:8px
    classDef external fill:#999999,color:#fff,stroke:#6b6b6b,stroke-width:2px,rx:8px,ry:8px

    customer["Customer\n\nA Cartly customer who reaches out for support via social media channels."]:::person
    agent["Support Agent\n\nA Cartly support agent who triages routed tickets, reviews AI-generated drafts, and approves responses."]:::person
    manager["Support Manager\n\nMonitors routing confidence, system KPIs, and manages support policy documents."]:::person
    
    copilot["Cartly Support Copilot\n\nAn autonomous support platform that automatically classifies inbound messages by intent and generates policy-grounded draft responses using a local RAG pipeline."]:::system
    
    socialMedia["Social Media Channels\n\nExternal platforms where customers send messages and ask questions."]:::external
    messaging["Messaging Bridge\n\nCommunication network used to bridge external social media messages and route them to internal department rooms."]:::external
    policyDocs["Policy Document Store\n\nMarkdown files containing company policies used for knowledge retrieval."]:::external

    customer -->|"Sends support requests to"| socialMedia
    socialMedia -->|"Messages bridged into"| messaging
    messaging -->|"Feeds raw messages for intent classification to"| copilot
    copilot -->|"Appends tags and routes messages to department rooms in"| messaging
    
    agent -->|"Requests response drafts and approves bounded actions in"| copilot
    manager -->|"Monitors system observability and fallbacks in"| copilot
    copilot -->|"Ingests knowledge from"| policyDocs
```
