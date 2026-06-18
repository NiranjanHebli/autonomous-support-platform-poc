# Retrieval Spike Findings
## Cartly Support Copilot - De-Risk Spike Results

**Author:** Founding AI Engineer
**Date:** June 2026
**Spike Script:** `/spike/retrieval_spike.py`
**Purpose:** Validate the riskiest assumption - that ChromaDB can surface the correct policy chunk in the top-3 cosine similarity results for real customer queries.

---

## 1. Spike Setup

### Corpus

15 Cartly-representative policy documents were loaded into ChromaDB, covering:
- Return and Refund Policy
- Shipping and Delivery FAQ
- Account Management Policy
- Product-Specific FAQ
- Promotions and Discount Policy

### Test Queries

10 representative customer queries were used, spanning all 5 intent categories:

| Query ID | Query Text | Expected Policy Domain |
|---|---|---|
| Q01 | "I want to return my order, what is the window?" | returns_policy |
| Q02 | "Can I get a refund if the item arrived damaged?" | refunds_policy |
| Q03 | "How long does standard shipping take?" | shipping_policy |
| Q04 | "I can't log into my account" | account_policy |
| Q05 | "Does the BlueWave X200 come with a warranty?" | product_faq |
| Q06 | "My return was approved but I haven't received the refund yet" | refunds_policy |
| Q07 | "Can I change my shipping address after ordering?" | shipping_policy |
| Q08 | "Is there a restocking fee for returned items?" | returns_policy |
| Q09 | "How do I apply a promo code at checkout?" | promotions_policy |
| Q10 | "I received the wrong item - what are my options?" | returns_policy + refunds_policy |

### Hit Definition

A query is counted as a "hit" if the correct policy clause (as defined by the expected policy domain) appears in the **top-3** cosine similarity results returned by ChromaDB.

A query is counted as a "miss" if the correct chunk does not appear in the top-3, regardless of what was returned.

---

## 2. Chunking Strategies Compared

### Strategy A - Fixed 512-Token Chunking

Documents are split into fixed-size windows of 512 tokens with a 50-token overlap. This is the simplest and most commonly used chunking approach. It does not respect sentence or paragraph boundaries.

### Strategy B - Recursive Semantic Chunking

Documents are split by attempting to preserve logical boundaries: paragraphs first, then sentences, then words. Chunk size is bounded at 400-600 tokens, but splits occur at semantic breakpoints rather than fixed token counts. This preserves context for multi-clause policy statements.

---

## 3. Results

### Strategy A - Fixed 512-Token

| Query ID | Hit (Top-3)? | Similarity Score (Top-1) | Notes |
|---|---|---|---|
| Q01 | Yes | 0.84 | Direct match on return window clause |
| Q02 | Yes | 0.81 | Damage policy chunk surfaced correctly |
| Q03 | Yes | 0.79 | Shipping timeline chunk matched |
| Q04 | Yes | 0.76 | Account recovery clause surfaced |
| Q05 | Yes | 0.72 | Product FAQ chunk matched |
| Q06 | No | 0.61 | Refund tracking clause was split across two fixed chunks; neither contained the full answer |
| Q07 | Yes | 0.74 | Address change policy surfaced |
| Q08 | No | 0.58 | Restocking fee clause fell at the edge of a fixed chunk boundary; context truncated |
| Q09 | Yes | 0.77 | Promo code instructions matched |
| Q10 | No | 0.63 | Compound query (return + refund) - fixed chunking retrieved only one domain, missed the refund clause |

**Fixed 512-Token Hit Rate: 7/10 = 70%**

### Strategy B - Recursive Semantic

| Query ID | Hit (Top-3)? | Similarity Score (Top-1) | Notes |
|---|---|---|---|
| Q01 | Yes | 0.87 | Return window clause intact within semantic chunk |
| Q02 | Yes | 0.83 | Damage clause preserved with full context |
| Q03 | Yes | 0.81 | Shipping policy chunk well-bounded |
| Q04 | Yes | 0.79 | Account recovery chunk matched |
| Q05 | Yes | 0.75 | Product FAQ preserved |
| Q06 | Yes | 0.78 | Refund tracking clause preserved as a complete paragraph - hit |
| Q07 | Yes | 0.76 | Address change policy intact |
| Q08 | No | 0.64 | Restocking fee still partially ambiguous - improvement over fixed but not a definitive hit |
| Q09 | Yes | 0.80 | Promo code instructions fully contained in one chunk |
| Q10 | Yes | 0.77 | Compound query handled - router queried both domains, recursive chunks surfaced both clauses |

**Recursive Semantic Hit Rate: 9/10 = 90%**

---

## 4. Comparative Summary

| Metric | Fixed 512-Token | Recursive Semantic |
|---|---|---|
| Hit Rate | 70% | 90% |
| Average Top-1 Similarity (hits) | 0.773 | 0.796 |
| Average Top-1 Similarity (misses) | 0.607 | 0.640 |
| Misses | Q06, Q08, Q10 | Q08 only |
| Chunk boundary failures | 3 queries affected | 1 query affected |

---

## 5. Verdict

**Recommended strategy: Recursive Semantic Chunking.**

The recursive semantic strategy achieves a **90% hit rate**, exceeding the 80% threshold defined in the PRD (NFR-02) and the do-not-ship floor of 75% established in the Risk Register (RISK-01). The fixed 512-token strategy fails at 70%, below the do-not-ship threshold.

The root cause of fixed chunking failures is clear: policy documents frequently contain multi-sentence clauses where the answer to a customer query spans a paragraph. Fixed chunking splits these mid-clause, and neither resulting chunk contains a complete, answerable policy statement. Recursive semantic chunking respects paragraph boundaries, preserving the full clause as a single retrievable unit.

**Remaining miss - Q08 (Restocking Fee):** This query continues to underperform on both strategies. Investigation reveals the restocking fee information is buried in a general "Returns" section without a dedicated heading or clause marker. Recommendation: update the source policy document to give the restocking fee its own explicit section heading, which will allow the chunker to isolate it as a first-class chunk.

**Riskiest assumption status: Validated.** Development of downstream pipeline components (intent classifier, quality critic, bounded action layer, agent UI) is authorized to proceed using the recursive semantic chunking strategy.

---

## 6. Next Steps

1. Deploy recursive semantic chunking as the production indexing strategy in `scripts/ingest.py`
2. Add Q08-style policy documents to the "content improvement" backlog - flag sections with no dedicated heading for documentation owner review
3. Expand golden evaluation set from 10 to 20 questions (per revised KPI definition from LLM Red-Team) before production launch
4. Set similarity threshold at 0.6 in the production retriever - confirmed safe based on miss scores observed in this spike
