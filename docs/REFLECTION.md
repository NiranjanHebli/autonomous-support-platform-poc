# Project Reflections

## Week 15 Reflections

### Which KPI was hardest to make measurable, and why?

The Groundedness Rate (>=90%) was the hardest KPI to make measurable in practice. The natural instrument - using the quality critic LLM to measure its own output - is circular: you are grading your own homework. The LLM red-team evaluation (see docs/LLM_REDTEAM.md) surfaced this problem explicitly: the critic may pass a draft that a human reviewer would flag as hallucinated. We resolved this by separating the production gate (LLM critic blocks bad drafts) from the measurement instrument (monthly human audit of minimum 50 drafts), but this requires ongoing operational commitment to keep the KPI meaningful beyond launch day.

### What is your riskiest assumption, and did the spike raise or lower your confidence?

The riskiest assumption is that a vector-similarity retriever can surface the correct policy chunk in the top-3 results for real customer queries. The retrieval spike (spike/retrieval_spike.py) tested this directly across 10 representative queries and two chunking strategies. The results were mixed: Fixed 512-token chunking achieved 80% (meeting the PRD target), while Recursive Semantic achieved 70% on the actual policy corpus - lower than anticipated. The spike was valuable not because it validated the assumption cleanly, but because it revealed that Q01 ("I want to return my order") and Q05 ("warranty") consistently missed across both strategies, pointing to content gaps in the policy documents themselves (no dedicated return-window or warranty sections). Overall confidence in retrieval as the right architecture is maintained, but the corpus quality issue must be addressed before production.

### If you had to cut scope to ship in half the time, what is the first thing that goes, and why?

The Quality Critic (secondary LLM pass) would be the first thing cut. It adds a full second LLM call per ticket - nearly doubling both latency and cost - and its primary benefit is preventing hallucinated drafts from reaching the agent. In an MVP with a well-constrained prompt and a low-temperature LLM, hallucination rates on domain-specific RAG with policy-grounded context are already low. The bounded action layer (Refund Approval Draft requiring explicit agent click) provides the safety net that matters most for the refund use case, and that can be shipped without the critic. The critic can be re-added in Sprint 2 once the baseline AHT improvement is confirmed in production.

## Week 16 Reflections

### Where did your system fail most: retrieval or generation? How do the metrics tell you which?

Initially, the system failed most frequently in retrieval. The baseline Ragas metrics clearly indicated this because Context Precision and Context Recall were our lowest scoring metrics (0.250 and 0.167 respectively). However, after applying semantic paragraph chunking and increasing top_k, we resolved these retrieval bottlenecks. Context Recall improved to 0.890 and Context Precision to 0.850. With retrieval fixed, generation (Faithfulness at 0.920) remained exceptionally strong.

### Did any metric look good while the answer was actually bad? What does that teach you about single-metric thinking?

Yes, Answer Relevancy occasionally scored high (e.g., 0.85+) even when the answer was fundamentally incorrect due to a hallucination. The LLM would confidently output a grammatically excellent response that perfectly addressed the structure of the user's question, scoring well on relevancy, but failing entirely on Faithfulness. This demonstrates that single-metric thinking is dangerous in RAG - Answer Relevancy without Faithfulness just means the system is a highly articulate liar.

### Which Week 15 target did you hit, miss, or have to revise after seeing real numbers?

We successfully hit all of our Week 15 targets after our final experiments. We achieved our Faithfulness target (0.920 >= 0.9) and Answer Relevancy target (0.880 >= 0.85) through strict system prompting. We also surpassed our Context Recall (0.890 >= 0.85) and Context Precision (0.850 >= 0.8) targets. We initially missed the retrieval targets in our baseline, but adopting a semantic chunking approach and tuning the prompt allowed us to meet and exceed all PRD thresholds without further revision.
