# Typo Robustness Evaluation Findings

**Author:** Niranjan Hebli & Bryson Gracias
**Date:** June 2026
**Purpose:** Evaluate how robust the TF-IDF / BM25 + LightGBM intent classification pipeline is to real-world customer query typos, and identify the minimum preprocessing needed to maintain acceptable accuracy.

---

## Setup

- **Test set:** 30 common customer support queries with deliberate typos injected
- **Hit definition:** Predicted intent matches the expected intent label
- **Metric:** Intent match rate (%) after typos; degradation measured against clean-text baseline

---

## Experiment Results

### Experiment 1 — TF-IDF + LightGBM (No Spell Correction)

**Vectorization:** TF-IDF (10k features, English stop words)
**Preprocessing:** None (raw typo-injected text)

| Metric | Result |
|---|---|
| Total queries | 30 |
| Correct intent matches | 5 |
| Intent match rate | **16.7%** |
| Degradation vs. clean text | **83.3%** |

**Conclusion:** TF-IDF relies on exact word-token matches. Typos shatter the vocabulary overlap between training and inference, causing near-total model failure. This confirms TF-IDF alone is not robust enough for production with untreated customer input.

---

### Experiment 2 — BM25 + Lemmatization + LightGBM (No Spell Correction)

**Vectorization:** BM25 with lemmatization
**Preprocessing:** None (raw typo-injected text)

| Metric | Result |
|---|---|
| Total queries | 30 |
| Correct intent matches | 5 |
| Intent match rate | **16.7%** |
| Degradation vs. clean text | **83.3%** |

**Conclusion:** BM25 with lemmatization performs identically to TF-IDF under raw typo conditions. Lemmatization only normalises valid words — it cannot repair unknown tokens created by typos. Spell correction is required upstream.

---

### Experiment 3 — BM25 + Lemmatization + TextBlob Spell Correction + LightGBM

**Vectorization:** BM25 with lemmatization
**Preprocessing:** TextBlob spell correction applied before vectorization

| Metric | Result |
|---|---|
| Total queries | 30 |
| Correct intent matches | 19 |
| Intent match rate | **63.3%** |
| Degradation vs. clean text | **36.7%** |

**Conclusion:** TextBlob spell correction recovers significant accuracy (from 16.7% -> 63.3%), but a 36.7% degradation rate is still too high for a production system. TextBlob's dictionary-based corrector cannot handle domain-specific terms (e.g., product names, order IDs) and misidentifies them as misspellings. A better approach (character n-gram subword tokenization or a domain-fine-tuned spell checker) is required before this pipeline can reach production KPI floors.

---

## Comparative Summary

| Experiment | Vectorizer | Spell Correction | Match Rate | Degradation |
|---|---|---|---|---|
| 1 | TF-IDF | None | 16.7% | 83.3% |
| 2 | BM25 + Lemmatization | None | 16.7% | 83.3% |
| 3 | BM25 + Lemmatization | TextBlob | 63.3% | 36.7% |

---

## Riskiest Assumption Confirmed

The evaluation confirms the riskiest assumption flagged in the Risk Register: **TF-IDF/BM25 vectorization does not generalise to user typos and slang.** Because these models rely on exact word matches, even mild typos (e.g., "pssword rset") produce tokens not seen during training, degrading decision tree splits in LightGBM.

---

## Recommended Next Steps

1. Evaluate character n-gram subword tokenization as a drop-in replacement for word-level TF-IDF — this would provide inherent typo tolerance without a separate spell-check step.
2. Investigate domain-fine-tuned spell correction (e.g., SymSpell with a customer support vocabulary) to improve on TextBlob's 63.3% ceiling.
3. Set a minimum acceptable production floor at **85% intent match rate under typo conditions** before deploying the classification model to live traffic.
