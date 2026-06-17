# Risk Register
## Cartly Support Copilot - v1.0

**Author:** Niranjan Hebli & Bryson Gracias 
**Last Updated:** June 2026

**Scoring:** Likelihood (1=Low, 2=Medium, 3=High) x Impact (1=Low, 2=Medium, 3=High, 4=Critical)

---

## Risk Table

| Risk ID | Risk Description | Likelihood | Impact | Risk Score | Mitigation Strategy |
|---|---|---|---|---|---|
| **RISK-01** | **Retrieval misses the policy doc (Riskiest Assumption)** - ChromaDB fails to surface the correct policy chunk in the top-3 results for a given customer query. This is the foundational technical assumption of the entire architecture. If retrieval fails, the LLM has no grounded source and will either hallucinate or fall back to a non-helpful "I don't know" response. Industry RAG systems on domain-specific corpora typically achieve 80-90% hit rates (Vectara, 2024), but this is highly sensitive to chunk size, embedding model, and query phrasing. | **High (3)** | **Critical (4)** | **12** | **Primary:** Run the de-risk spike (`/spike/retrieval_spike.py`) across 10 representative queries before building any downstream components. If hit rate is below 75%, do not proceed - re-chunk using recursive/semantic strategy and re-run. **Secondary:** Set a similarity score threshold of 0.6 or above; below threshold, block draft generation and route to human-only mode. **Monitoring:** Weekly automated eval against a 20-question golden set; alert if hit rate drops below 80%. |
| **RISK-02** | **LLM approves refund outside of policy scope (Safety risk)** - The generative model produces a draft that recommends a refund for an amount, time window, or product category not covered by the retrieved policy clause. This is a direct financial and legal liability risk. For example, if the model hallucinates "30-day return window" when the actual policy is 14 days, and the agent sends it, Cartly is operationally bound. | **Medium (2)** | **High (3)** | **6** | **Primary:** Quality Critic (secondary LLM pass) explicitly checks "Does the draft make any claim not in the retrieved context?" and outputs `is_grounded: bool`. If false, the Refund Approval Draft is suppressed. **Secondary:** Refund Approval Draft requires an explicit agent click - no automated send. **Tertiary:** All refund draft decisions logged with chunk ID and critic verdict for audit. |
| **RISK-03** | **PII leakage to external API** - A failure in the local PII masking layer (regex miss or NER model failure) could result in raw customer data (name, email, order ID) being sent to the OpenAI API, violating Cartly's data handling obligations. | **Medium (2)** | **Medium (2)** | **4** | **Primary:** PII masker runs locally before any external API call; pipeline halts on masking failure. **Secondary:** Audit log captures the masked ticket text (not raw) for review. **Monitoring:** Monthly random audit of 50 logged tickets verifies zero raw PII in API call payloads. |
| **RISK-04** | **System latency exceeds acceptable threshold** - Complex multi-step pipeline (PII masking + classification + retrieval + generation + critic) may exceed the 3-second P95 target, eroding agent trust if the Copilot feels slower than manual tab-switching. | **Low (1)** | **Critical (4)** | **4** | **Primary:** Async parallel execution of retrieval and prompt assembly where dependencies allow. **Secondary:** Caching of embedding vectors for repeated queries. **Monitoring:** P95 latency tracked per pipeline stage; alert if any stage exceeds 1.5 seconds independently. |
| **RISK-05** | **Stale knowledge base: Policy updates not re-indexed** - Cartly's support policies change regularly: return windows adjust during promotions, shipping fees change, new product categories are added. If the ChromaDB vector store is not re-indexed when these changes occur, agents will confidently present outdated information grounded in old policy chunks. This is an operational risk that grows over time. | **Medium (2)** | **High (3)** | **6** | **Primary:** GitHub Actions webhook triggers an automatic re-index whenever a file in `/data/policies/` is modified on `main`. **Secondary:** Each chunk is stored with an `indexed_at` timestamp and `doc_commit_hash`. The weekly eval script checks for chunks older than 30 days and flags them for review. **Tertiary:** Slack alert to `#support-ai-ops` confirms every successful re-index and reports the total document count and index freshness date. |

---

## Risk Matrix (Visual)

```
IMPACT →
              Low (1)    Medium (2)    High (3)    Critical (4)
Likelihood ↓
High (3)                  RISK-03                    RISK-01
Medium (2)                              RISK-02      RISK-05
Low (1)                                              RISK-04
```

---

## Riskiest Assumption Summary

**RISK-01 (Retrieval Miss) is the Highest Riskiest Assumption** because the entire Copilot architecture depends on ChromaDB returning the correct policy chunk. If this assumption fails, the LLM has nothing grounded to work with and the system degrades to either hallucination or useless "I don't know" responses. This assumption is tested directly by the de-risk spike in `/spike/`. If the spike shows hit rate below 75%, we must re-evaluate the chunking strategy before any further development.
