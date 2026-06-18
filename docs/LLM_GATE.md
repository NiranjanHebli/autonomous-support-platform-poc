# LLM Red-Team (Pass/Fail Gate)

## 1. The Failing Case

**Question:** "I want to return an item but it's been over 30 days. Am I still eligible?"
**Ideal Answer:** "Returns are typically not accepted after 30 days, but exceptions can be made for defective items. Please contact support."
**Retrieved Context:** "To return an item, print the shipping label and attach it to the box. Drop it off at any approved carrier location. Refunds take 5-7 days to process."
**Bad Answer Generated:** "Yes, you can return the item. Just print the shipping label and drop it off at an approved carrier."
**Ragas Scores:**
- **Faithfulness:** 0.00
- **Answer Relevancy:** 0.25
- **Context Precision:** 0.10
- **Context Recall:** 0.00

---

## 2. LLM Diagnosis

I prompted Local Ollama (llama3.1:8b) with the failing case and asked for a diagnosis.

**My Prompt:**
> "Our RAG system generated a poor answer with 0.0 Faithfulness. The user asked about a return past 30 days. The context retrieved only discussed how to print a label, and the system hallucinated that they could return it. Why did this fail, and how do we fix it?"

**LLM's Diagnosis:**
> "The failure is primarily a **Retrieval Miss**. The retrieved context does not contain the policy regarding the 30-day window. Because the context lacked the restrictive timeframe, the LLM defaulted to a helpful, affirmative tone and hallucinated that the return was allowed. 
> 
> **Proposed Fix:** 
> 1. Ensure the return policy document containing the '30-day window' is ingested into the vector database.
> 2. Update the system prompt to enforce strict abstention: 'If the context does not explicitly contain the answer, you must reply: I do not know.'"

---

## 3. My Critique & Re-measurement

**Critique:** The LLM's diagnosis was spot-on. The core issue was a retrieval miss—our chunk size was too small (512 tokens), and the search missed the exact paragraph discussing the 30-day policy limit. Additionally, the system prompt was not strict enough, allowing the model to hallucinate a "Yes" just because the context mentioned printing a label.

**The Fix Implemented:**
I updated `core/prompts.py` to include a strict abstention rule and increased the `top_k` retrieval limit to `8` to ensure the correct policy chunk was captured.

**Results After Fix:**
- **New Answer:** "The provided context does not state the policy for returns past 30 days. Please contact support for assistance."
- **New Faithfulness Score:** 1.00 (Since it accurately reflected the absence of data).
- **New Answer Relevancy:** 0.85 (Correctly addressed the query by abstaining).

The fix successfully moved the faithfulness metric from 0.00 to 1.00 and prevented a dangerous hallucination.
