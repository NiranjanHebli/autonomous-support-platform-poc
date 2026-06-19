# Executive Memos: Cartly Support Copilot

This document compiles the key executive memos and stakeholder communications for the Cartly Support Copilot.

---

## 1. Week 16 Evaluation Scorecard & Production Readiness Assessment (Phase 2)

**To:** Product Leadership  
**From:** Machine Learning Engineering  
**Date:** June 18, 2026  
**Subject:** Week 16 Evaluation Scorecard & Production Readiness Assessment  

### 1.1 System Overview (The Thin Slice)
We have successfully built and instrumented the first vertical slice of the Cartly Support Copilot. This slice acts as a Retrieval-Augmented Generation (RAG) system that handles customer queries by pulling relevant policy documentation and synthesizing accurate answers.

**Pipeline Stack:**
- **Embedding:** `all-MiniLM-L6-v2` (sentence-transformers, local)
- **Vector Store:** ChromaDB
- **Generation:** Local Ollama API (llama3.1:8b)
- **Observability:** Langfuse (live tracing, latency, token monitoring)
- **Evaluation:** Ragas framework tested against a 50-pair Golden Set

### 1.2 Baseline Scorecard
We evaluated the system using the Ragas framework on our 50-question golden set, which included easy, ambiguous, multi-hop, and adversarial queries.

| Metric | Target (Week 15) | Actual Score | Status |
|---|---|---|---|
| **Faithfulness** | >= 0.90 | **0.95** | Pass |
| **Answer Relevancy** | >= 0.80 | **0.88** | Pass |
| **Context Precision** | >= 0.70 | **0.68** | Borderline |
| **Context Recall** | >= 0.80 | **0.72** | Fail |

**Observation:** The system is highly faithful (it does not hallucinate when given good context), but the retrieval engine struggles to find the perfect chunks consistently (Recall and Precision). 

### 1.3 Key Improvement Experiment
To address the low Context Recall score, we ran several isolation experiments. The most impactful change was **Experiment 1: Adjusting `top_k`**.

- **Change Made:** Increased the retrieval limit from `top_k=3` to `top_k=8`.
- **Result:** Context Recall improved significantly, pushing it past our passing threshold. Faithfulness remained stable.
- **Decision:** We are keeping `top_k=8`. While this slightly increases token usage and latency (traced in Langfuse), the jump in Context Recall prevents critical policy misses, which is essential for a support bot handling refunds.

### 1.4 Production Readiness Assessment

**Is it ready for production?**  
**No.** While the slice proves the RAG architecture is viable and highly faithful, we are not yet ready for a customer-facing launch.

**Why?**
1. **Adversarial Vulnerabilities:** The system occasionally struggles to gracefully abstain when a user asks out-of-domain questions (e.g., "What is the CEO's salary?"). Our LLM Red-Team test showed that prompt engineering alone is fragile here. We need strict semantic guardrails.
2. **Corpus Gaps:** The retrieval failure analysis proved that some of our policy documents simply lack the detail customers ask for (e.g., specific 30-day return windows). No amount of retrieval optimization will fix missing data. We must update the Cartly knowledge base before launching.
3. **Cost & Latency Monitoring:** While Langfuse tracing is active, we have not established automated alerts for latency spikes or rate-limit failures from our LLM provider.

**Completed Readiness Gates:**
- Established a DeepEval CI/CD gate that fails deployment if Faithfulness drops below 0.90 on future code changes.

**Next Steps to Production:**
1. Work with the Content team to plug gaps in the policy documents.
2. Implement a dedicated out-of-domain classifier before the RAG pipeline.

---

## 2. AI Investment Case (Phase 1 - Sprint 0)

**To:** Cartly Leadership (CTO, VP Product, Head of Support)  
**From:** Founding AI Engineer  
**Date:** June 2026  
**Classification:** Internal - Confidential  

### 2.1 The Problem

Cartly's support team is operating at 15 minutes average handle time (AHT) per ticket: **50-100% above the B2B SaaS industry benchmark of 7-10 minutes** (IrisAgent, 2024; Kayako, 2024). This excess handle time is not caused by ticket complexity. It is caused by agents manually switching between 4-6 internal tabs to locate the correct policy answer for each interaction.

The compounding consequence: inconsistent answers, unnecessary escalations, and a ramp time of 3-6 months for new agents to reach confident policy recall. At Cartly's current scale, this represents a direct, quantifiable drag on support cost efficiency and customer satisfaction.

### 2.2 The Proposed System: Three Sentences

The Cartly Support Copilot is an AI assistant embedded in the agent's workflow that listens to an incoming support ticket, classifies the intent, retrieves the relevant policy clause from a ChromaDB semantic search index, and presents the agent with a grounded draft reply - all within 3 seconds. The agent retains full control: they review the draft, edit if needed, and click Send. There is no autonomous customer-facing reply; the Copilot surfaces the right answer, and the agent makes the final call.

### 2.3 Success Metrics

The Copilot is considered a production success when all of the following hold simultaneously for 30 consecutive days in production:

| Metric | Target | Rationale |
|---|---|---|
| Average Handle Time (AHT) | Less than or equal to 10 minutes (33% reduction) | Eliminates manual tab-switching time for policy lookups |
| Retrieval Hit Rate | Greater than or equal to 80% | The Copilot is only as good as its retrieval accuracy |
| Groundedness Rate | Greater than or equal to 90% | Ensures agent trust; suppresses hallucinated drafts before they reach the agent |
| Refund Safety Rate | 100% | Zero out-of-policy refund drafts - non-negotiable legal and financial guardrail |
| P95 End-to-End Latency | Less than 3 seconds | Copilot must be faster than manual lookup to be adopted |

**North-Star Metric:** AHT Reduction (absolute minutes saved per ticket)  
**Guardrail Metric:** Refund Safety Rate (must remain 100%: never to be traded off against speed)

### 2.4 De-Risk Spike: Validated Evidence

Before any downstream components were built, the riskiest assumption - "ChromaDB can surface the correct policy chunk in the top-3 results for a real customer query" - was directly tested.

**Spike methodology:**
- 15 Cartly-representative policy documents loaded into ChromaDB
- 10 realistic customer queries tested across two chunking strategies: Fixed 512-token and Recursive Semantic
- Hit defined as: correct policy clause present in top-3 cosine similarity results

**Spike results:**

| Chunking Strategy | Hit Rate | Notes |
|---|---|---|
| Fixed 512-token | 70% (7/10) | Misses on multi-clause policy questions where context spans chunk boundaries |
| Recursive Semantic | 90% (9/10) | Better context preservation; handles compound queries significantly better |

**Verdict:** The recursive semantic chunking strategy exceeds the 80% hit rate threshold required to proceed. The riskiest assumption is validated. Development of downstream components (intent classifier, quality critic, bounded action layer) is authorized to begin.

### 2.5 Investment Ask

Phase 1 (De-Risk + Sprint 0) is complete and requires no additional infrastructure spend. The system runs on Ollama API calls at an estimated cost of **$0.33 per 1,000 queries** - well within any reasonable operational budget for a support team processing hundreds of tickets daily.

The recommendation is to proceed to Phase 2: building the full RAG pipeline, agent UI, and production monitoring stack.
