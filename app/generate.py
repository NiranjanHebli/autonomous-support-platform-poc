"""
Assembles the RAG prompt using retrieved policy chunks and calls
the centralized LLM to produce a grounded draft response with citations.

Usage (standalone smoke test):
    uv run python app/generate.py
"""

import sys
from pathlib import Path

# Ensure project root is on the path so `core` is importable when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.retrieve import retrieve

import json
from core.llm_core import generate_completion
from core.prompts import SYSTEM_PROMPT, CONTEXT_TEMPLATE, USER_TEMPLATE, CRITIC_PROMPT
from core.config import DEFAULT_TOP_K


def build_prompt(query: str, chunks: list[dict]) -> tuple[str, str]:
    """Assemble the user message with retrieved context. Returns (user_message, context_block)."""
    context_parts = [
        CONTEXT_TEMPLATE.format(
            i=i + 1, doc_name=c["doc_name"], chunk_id=c["chunk_id"], text=c["text"]
        )
        for i, c in enumerate(chunks)
    ]
    context_block = "\n\n".join(context_parts)
    return USER_TEMPLATE.format(context_block=context_block, query=query), context_block


def generate(query: str, chunks: list[dict]) -> dict:
    """
    Call the LLM with the assembled RAG prompt, parse JSON, and run the Quality Critic.
    """
    user_message, context_block = build_prompt(query, chunks)

    max_retries = 2
    for attempt in range(max_retries):
        # 1. Generate Draft
        result = generate_completion(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=500,
            temperature=0.0,
        )

        # Clean LLM output of potential markdown wrappers
        raw_text = result["answer"].strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        raw_text = raw_text.strip()

        try:
            parsed = json.loads(raw_text)
            draft_reply = parsed.get("draft_reply", raw_text)
            citations = parsed.get("citations", [])
        except Exception:
            draft_reply = raw_text
            citations = []

        # 2. Critic Check
        critic_prompt = CRITIC_PROMPT.format(
            context_block=context_block, draft=draft_reply
        )
        critic_res = generate_completion(
            system_prompt="You are a strict JSON-only JSON API.",
            user_message=critic_prompt,
            max_tokens=200,
            temperature=0.0,
        )

        critic_raw = critic_res["answer"].strip()
        if critic_raw.startswith("```json"):
            critic_raw = critic_raw[7:]
        if critic_raw.startswith("```"):
            critic_raw = critic_raw[3:]
        if critic_raw.endswith("```"):
            critic_raw = critic_raw[:-3]
        critic_raw = critic_raw.strip()

        try:
            critic_json = json.loads(critic_raw)
            is_grounded = critic_json.get("is_grounded", True)
            violation = critic_json.get("violation", None)
        except Exception:
            is_grounded = True
            violation = None

        if is_grounded or attempt == max_retries - 1:
            break

        # Append feedback for next attempt
        user_message += f"\n\nSystem QA Feedback on your previous draft: {violation}\nPlease rewrite your response to fix this error and output valid JSON."

    # Extract cited chunk IDs
    cited_chunks = []
    for cit in citations:
        chunk_id = cit.get("source_chunk", "")
        if chunk_id:
            cited_chunks.append(chunk_id)

    if not cited_chunks:
        cited_chunks = [c["chunk_id"] for c in chunks]

    result["answer"] = draft_reply
    result["citations"] = citations
    result["cited_chunks"] = cited_chunks
    result["is_grounded"] = is_grounded
    result["critic_violation"] = violation
    return result


if __name__ == "__main__":

    query = "Can I get a refund if the item arrived damaged?"
    chunks = retrieve(query, top_k=DEFAULT_TOP_K)
    result = generate(query, chunks)
    print(f"\nQuery: {query}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nCited chunks: {result['cited_chunks']}")
    print(f"Model: {result['model']}")
    print(
        f"Tokens: {result['prompt_tokens']} prompt + {result['completion_tokens']} completion"
    )
