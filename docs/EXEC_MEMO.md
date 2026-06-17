# Executive Memo
## Cartly Support Copilot - AI Investment Case

**To:** Cartly Leadership (CTO, VP Product, Head of Support)
**From:** Founding AI Engineer
**Date:** June 2026
**Classification:** Internal - Confidential

---

## The Problem

Cartly's support team is operating at 15 minutes average handle time (AHT) per ticket: **50-100% above the B2B SaaS industry benchmark of 7-10 minutes** (IrisAgent, 2024; Kayako, 2024). This excess handle time is not caused by ticket complexity. It is caused by agents manually switching between 4-6 internal tabs to locate the correct policy answer for each interaction.

The compounding consequence: inconsistent answers, unnecessary escalations, and a ramp time of 3-6 months for new agents to reach confident policy recall. At Cartly's current scale, this represents a direct, quantifiable drag on support cost efficiency and customer satisfaction.

---

## The Proposed System: Three Sentences

The Cartly Support Copilot is an AI assistant embedded in the agent's workflow that listens to an incoming support ticket, classifies the intent, retrieves the relevant policy clause from a ChromaDB semantic search index, and presents the agent with a grounded draft reply - all within 3 seconds. The agent retains full control: they review the draft, edit if needed, and click Send. There is no autonomous customer-facing reply; the Copilot surfaces the right answer, and the agent makes the final call.

---

## Success Metrics

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

---

## De-Risk Spike: Validated Evidence

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

---

## Investment Ask

Phase 1 (De-Risk + Sprint 0) is complete and requires no additional infrastructure spend. The system runs on OpenAI API calls at an estimated cost of **$0.33 per 1,000 queries** - well within any reasonable operational budget for a support team processing hundreds of tickets daily.

The recommendation is to proceed to Phase 2: building the full RAG pipeline, agent UI, and production monitoring stack.
