# Cartly Support Copilot — Baseline Ragas Scorecard

**LLM:** Local Ollama llama3.1:8b
**Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (local)
**Vector Store:** ChromaDB (cosine, top-k=5)
**Golden Set:** 50 Q&A pairs (20 easy, 10 ambiguous, 10 multi-hop, 10 adversarial)

---

## Results vs. Week 15 PRD Targets

| Metric | Actual | PRD Target | Pass Floor | Status |
|---|---|---|---|---|
| Faithfulness | 0.920 | >= 0.9 | >= 0.8 | PASS (meets target) |
| Answer Relevancy | 0.880 | >= 0.85 | >= 0.8 | PASS (meets target) |
| Context Precision | 0.850 | >= 0.8 | >= 0.7 | PASS (meets target) |
| Context Recall | 0.890 | >= 0.85 | >= 0.8 | PASS (meets target) |

---

## Notes

- Adversarial queries should produce 'I cannot answer' responses.
  Faithfulness on these rows will be high if the model correctly abstains.
- See `eval/results.csv` for per-question breakdown.
- See `experiments/RESULTS.md` for improvement experiments.