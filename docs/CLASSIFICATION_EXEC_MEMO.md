# Executive Memo: Support Platform Intent Classification

**To:** Project Leadership
**Date:** June 18, 2026
**Subject:** Classification Evaluation Framework, Baseline Performance, and Production Readiness

---

## 1. The Evaluation Slice Built
We successfully implemented a fully automated evaluation pipeline (`eval/` suite) for our LightGBM-based text classification models. This framework automatically samples and stratifies customer support queries from the Hugging Face Bitext dataset, yielding an evenly balanced holdout set of 300 test cases. We integrated five critical multi-class metrics (Accuracy, Macro Precision, Macro Recall, Macro F1-Score, and MCC) to rigorously evaluate both high-level **Category** and specific **Intent** predictions. 

## 2. Baseline Scorecard
On a clean dataset, the baseline model achieved near-perfect performance:
*   **Category Classification:** 100% Accuracy, 1.0000 MCC
*   **Intent Classification:** 99.67% Accuracy, 0.9965 MCC

While excellent, these metrics suggested the model was evaluated on perfectly formatted, noise-free text that does not reflect real-world customer inputs.

## 3. High-Impact Experiment: Real-World Noise Injection
To understand true model robustness, we ran a **Noise Injection Experiment** (`eval/add_noise.py`) that intentionally degraded 60% of the test queries by introducing common typos, dropped characters, and misspellings (e.g., "password" → "pssword", missing letters in short words). 

This experiment immediately produced a more realistic scorecard:
*   **Category Accuracy** dropped from 100% to **94.00%** (MCC: 0.9329).
*   **Intent Accuracy** dropped from 99.67% to **90.00%** (MCC: 0.8979).

**Takeaway:** This experiment proved that while the BM25 + LightGBM pipeline is strong, it is sensitive to out-of-vocabulary terms caused by typos. It moved the metric significantly and highlighted the necessity of robust preprocessing (like the `TextBlob` spell-correction tested during our Spike).

## 4. Production Readiness Assessment

### What *IS* Production-Ready
*   **The Evaluation Framework:** The automated stratification, noise injection, and multi-class metric calculation pipeline is highly reliable and easily reproducible via `uv run eval/run.ps1`.
*   **High-Level Category Routing:** At 94% accuracy even with messy inputs, the `model_category.pkl` is robust enough for initial tier-1 ticket routing. 

### What *ISN'T* Production-Ready
*   **Intent Granularity without Spell-Correction:** The drop to 90% accuracy on specific Intents under noisy conditions means 1 in 10 messy customer queries will be misclassified. Before deploying the Intent model to production, we must integrate a fast, reliable spell-checker into the prediction pipeline, or migrate to sub-word tokenization (e.g., a fast transformer model or BPE tokenizer) to handle misspellings natively. 
*   **Artifact Management:** The `.pkl` models are currently large and handled locally. A proper ML model registry or cloud bucket should be used to pull these artifacts securely during deployment.
