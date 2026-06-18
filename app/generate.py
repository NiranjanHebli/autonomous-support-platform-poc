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

from core.llm_core import generate_completion
from core.prompts import SYSTEM_PROMPT, CONTEXT_TEMPLATE, USER_TEMPLATE


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Assemble the user message with retrieved context."""
    context_parts = [
        CONTEXT_TEMPLATE.format(i=i + 1, doc_name=c["doc_name"], text=c["text"])
        for i, c in enumerate(chunks)
    ]
    context_block = "\n\n".join(context_parts)
    return USER_TEMPLATE.format(context_block=context_block, query=query)


def generate(query: str, chunks: list[dict]) -> dict:
    """
    Call the LLM with the assembled RAG prompt.

    Returns a dict containing:
        - answer (str): The LLM's draft response
        - cited_chunks (list[str]): chunk_ids of the chunks used as context
        - prompt_tokens (int)
        - completion_tokens (int)
        - model (str)
    """
    user_message = build_prompt(query, chunks)

    # Use the centralized LLM function
    result = generate_completion(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        max_tokens=400,
        temperature=0.2,
    )

    result["cited_chunks"] = [c["chunk_id"] for c in chunks]
    return result


if __name__ == "__main__":

    query = "Can I get a refund if the item arrived damaged?"
    chunks = retrieve(query, top_k=3)
    result = generate(query, chunks)
    print(f"\nQuery: {query}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nCited chunks: {result['cited_chunks']}")
    print(f"Model: {result['model']}")
    print(
        f"Tokens: {result['prompt_tokens']} prompt + {result['completion_tokens']} completion"
    )
