"""
Orchestrates the full RAG pipeline: retrieve -> generate.
This is the single entrypoint used by:
  - eval/evaluate.py (Ragas scoring)
  - experiments/ (metric-driven experiments)
  - Manual smoke tests

Langfuse @observe() decorators trace every run automatically.

Usage:
    uv run python app/pipeline.py "How do I cancel my order?"
"""

import sys
from pathlib import Path

# Ensure project root is on the path so `core`, `app`, and `observability`
# are importable when running this script directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.retrieve import retrieve
from app.generate import generate
from core.config import DEFAULT_TOP_K
from observability.langfuse_setup import get_langfuse_decorator

observe = get_langfuse_decorator()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


@observe(name="retrieve_step")
def _retrieve(query: str, top_k: int) -> list[dict]:
    """Wrapped retrieval step — traced as a separate span in Langfuse."""
    return retrieve(query, top_k=top_k)


@observe(name="generate_step")
def _generate(query: str, chunks: list[dict]) -> dict:
    """Wrapped generation step — traced as a separate span in Langfuse."""
    return generate(query, chunks)


@observe(name="rag_pipeline")
def run(query: str, top_k: int = DEFAULT_TOP_K) -> dict:
    """
    Run the full RAG pipeline for a single query.

    Returns:
        {
            "query": str,
            "answer": str,
            "contexts": list[str],       # raw chunk texts (for Ragas)
            "cited_chunks": list[str],   # chunk IDs
            "retrieved_chunks": list[dict],
            "prompt_tokens": int,
            "completion_tokens": int,
        }
    """
    chunks = _retrieve(query, top_k=top_k)
    result = _generate(query, chunks)

    return {
        "query": query,
        "answer": result["answer"],
        "citations": result.get("citations", []),
        "contexts": [c["text"] for c in chunks],  # Ragas needs raw texts
        "cited_chunks": result["cited_chunks"],
        "retrieved_chunks": chunks,
        "prompt_tokens": result["prompt_tokens"],
        "completion_tokens": result["completion_tokens"],
    }


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How do I cancel my order?"
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    output = run(query)
    print(f"\nAnswer:\n{output['answer']}")
    print(f"\nRetrieved from: {[c['doc_name'] for c in output['retrieved_chunks']]}")
    print(
        f"Tokens used: {output['prompt_tokens']} prompt + {output['completion_tokens']} completion"
    )
