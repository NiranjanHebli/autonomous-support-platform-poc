# Risk Register
## Cartly Support Copilot - v1.0

**Author:** Niranjan Hebli & Bryson Gracias
**Last Updated:** June 2026

**Scoring:** Likelihood (1=Low, 2=Medium, 3=High) x Impact (1=Low, 2=Medium, 3=High, 4=Critical)

---

## Part 1 — Cartly Support Copilot (RAG Pipeline)

### Risk Table

| Risk ID | Risk Description | Likelihood | Impact | Risk Score | Mitigation Strategy |
|---|---|---|---|---|---|
| **RISK-01** | **Retrieval misses the policy doc (Riskiest Assumption)** — ChromaDB fails to surface the correct policy chunk in the top-5 results for a given customer query. This is the foundational technical assumption of the entire architecture. If retrieval fails, the LLM has no grounded source and will either hallucinate or fall back to a non-helpful "I don't know" response. Industry RAG systems on domain-specific corpora typically achieve 80-90% hit rates (Vectara, 2024), but this is highly sensitive to chunk size, embedding model, and query phrasing. | **High (3)** | **Critical (4)** | **12** | **Primary:** Run the de-risk spike (`/spike/retrieval_spike.py`) across 10 representative queries before building any downstream components. If hit rate is below 75%, do not proceed — re-chunk using recursive/semantic strategy and re-run. **Secondary:** Set a similarity score threshold of 0.6 or above; below threshold, block draft generation and route to human-only mode. **Monitoring:** Weekly automated eval against a 20-question golden set; alert if hit rate drops below 80%. |
| **RISK-02** | **LLM approves refund outside of policy scope (Safety risk)** — The generative model produces a draft that recommends a refund for an amount, time window, or product category not covered by the retrieved policy clause. This is a direct financial and legal liability risk. | **Medium (2)** | **High (3)** | **6** | **Primary:** Quality Critic (secondary LLM pass) explicitly checks "Does the draft make any claim not in the retrieved context?" and outputs `is_grounded: bool`. If false, the Refund Approval Draft is suppressed. **Secondary:** Refund Approval Draft requires an explicit agent click — no automated send. **Tertiary:** All refund draft decisions logged with chunk ID and critic verdict for audit. |
| **RISK-03** | **PII leakage to LLM API** — A failure in the local PII masking layer (regex miss or NER model failure) could result in raw customer data (name, email, order ID) being sent to the LLM API (Ollama), violating Cartly's data handling obligations. | **Medium (2)** | **Medium (2)** | **4** | **Primary:** PII masker runs locally before any LLM API call; pipeline halts on masking failure. **Secondary:** Audit log captures the masked ticket text (not raw) for review. **Monitoring:** Monthly random audit of 50 logged tickets verifies zero raw PII in LLM API call payloads. |
| **RISK-04** | **System latency exceeds acceptable threshold** — Complex multi-step pipeline (PII masking + classification + retrieval + generation + critic) may exceed the 3-second P95 target, eroding agent trust if the Copilot feels slower than manual tab-switching. | **Low (1)** | **Critical (4)** | **4** | **Primary:** Async parallel execution of retrieval and prompt assembly where dependencies allow. **Secondary:** Caching of embedding vectors for repeated queries. **Monitoring:** P95 latency tracked per pipeline stage; alert if any stage exceeds 1.5 seconds independently. |
| **RISK-05** | **Stale knowledge base: Policy updates not re-indexed** — Cartly's support policies change regularly: return windows adjust during promotions, shipping fees change, new product categories are added. If the ChromaDB vector store is not re-indexed when these changes occur, agents will confidently present outdated information grounded in old policy chunks. | **Medium (2)** | **High (3)** | **6** | **Primary:** GitHub Actions webhook triggers an automatic re-index whenever a file in `/data/policies/` is modified on `main`. **Secondary:** Each chunk is stored with an `indexed_at` timestamp and `doc_commit_hash`. **Tertiary:** Slack alert to `#support-ai-ops` confirms every successful re-index. |

### Risk Matrix

```
IMPACT ->
              Low (1)    Medium (2)    High (3)    Critical (4)
Likelihood ↓
High (3)                  RISK-03                    RISK-01
Medium (2)                              RISK-02      RISK-05
Low (1)                                              RISK-04
```

### Riskiest Assumption Summary

**RISK-01 (Retrieval Miss) is the Highest Riskiest Assumption** because the entire Copilot architecture depends on ChromaDB returning the correct policy chunk. If this assumption fails, the LLM has nothing grounded to work with and the system degrades to either hallucination or useless "I don't know" responses. This assumption is tested directly by the de-risk spike in `/spike/`. If the spike shows hit rate below 75%, we must re-evaluate the chunking strategy before any further development.

---

## Part 2 — Classification Pipeline (Social Media Routing, TF-IDF / LightGBM)

### Risk Table

| Risk ID | Risk Description | Likelihood | Impact | Mitigation Strategy |
|---|---|---|---|---|
| **RISK-C01** | **TF-IDF Semantic Limitations** — Exact-match vectorization fails to capture synonyms or paraphrasing not seen in the Bitext training data | High | Medium | Re-train with a fallback sentence-transformer model if TF-IDF fails to catch synonyms/paraphrasing. Confirmed by typo evaluation (see [FINDINGS.md](FINDINGS.md)). |
| **RISK-C02** | **Social Media Rate Limiting** — Burst message volume causes Matrix API throttling | Medium | High | Implement exponential backoff in the Matrix client's `send_message` and `get_messages` functions. |
| **RISK-C03** | **Class Imbalance in Training Data** — Certain categories consistently underperform due to fewer training examples | Medium | Medium | Use `class_weight='balanced'` in LightGBM if specific categories fall below the F1 floor. Monitor per-class precision/recall in `score.py`. |
| **RISK-C04** | **Out-of-Domain / Gibberish Messages** — Non-support messages (spam, greetings) routed as low-confidence predictions | High | Low | The 0.60 confidence threshold in `score.py` catches most of these and safely defaults to `UNDEFINED`. Confirmed working in spike. |
| **RISK-C05** | **Slow Matrix Room Joins** — Cold-join latency adds overhead on first contact with a room | Low | Medium | Cache joined room states locally. Only call `client.join_room()` when explicitly necessary. |

### Riskiest Assumption (Classification Pipeline)

**That TF-IDF vectorization generalises well to actual user typos and slang.**

Because TF-IDF relies on exact word matches, user messages with severe typos (e.g., `"pssword rset"`) may not trigger the correct LightGBM decision trees, unlike an embedding model which captures semantic closeness.

**Status:** Confirmed as a real risk by the typo evaluation (see [FINDINGS.md](FINDINGS.md)). Degradation rate of 83.3% without spell correction; 36.7% with TextBlob. Further mitigation required before production deployment.
