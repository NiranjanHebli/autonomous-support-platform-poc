# Cartly Support Copilot — Baseline Ragas Scorecard

**LLM:** Local Ollama llama3.1:8b
**Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (local)
**Vector Store:** ChromaDB (cosine, top-k=5)
**Golden Set:** 50 Q&A pairs (20 easy, 10 ambiguous, 10 multi-hop, 10 adversarial)

---

## Results vs. Week 15 PRD Targets

| Metric | Actual | PRD Target | Pass Floor | Status |
|---|---|---|---|---|
| Faithfulness | nan | >= 0.9 | >= 0.8 | FAIL (below floor) |
| Answer Relevancy | 0.679 | >= 0.85 | >= 0.8 | FAIL (below floor) |
| Context Precision | nan | >= 0.8 | >= 0.7 | FAIL (below floor) |
| Context Recall | 0.583 | >= 0.85 | >= 0.8 | FAIL (below floor) |

---

## Notes

- Adversarial queries should produce 'I cannot answer' responses.
  Faithfulness on these rows will be high if the model correctly abstains.
- See `eval/results.csv` for per-question breakdown.
- See `experiments/RESULTS.md` for improvement experiments.