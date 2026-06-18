"""
Retrieves the top-k most semantically similar policy chunks from ChromaDB
for a given query, using sentence-transformers (all-MiniLM-L6-v2, local).

Usage (standalone smoke test):
    uv run python app/retrieve.py "How do I return an item?"
"""

import sys
from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Ensure project root is on the path so `core` is importable when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    DEFAULT_TOP_K,
)


def get_collection():
    """Return the ChromaDB collection. Raises if not ingested yet."""
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"ChromaDB store not found at {CHROMA_DIR}. "
            "Run `uv run python app/ingest.py` first."
        )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
    return client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Query ChromaDB and return the top-k chunks.

    Returns a list of dicts, each containing:
        - chunk_id (str)
        - doc_name (str)
        - text (str)
        - similarity_score (float, 0–1, higher = more similar)
    """
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    ids = results["ids"][0]
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    # ChromaDB cosine distance: 0 = identical, 2 = opposite. Convert to similarity.
    distances = results["distances"][0]

    for chunk_id, text, meta, dist in zip(ids, docs, metas, distances):
        similarity = 1.0 - (dist / 2.0)
        chunks.append(
            {
                "chunk_id": chunk_id,
                "doc_name": meta.get("doc_name", "unknown"),
                "text": text,
                "similarity_score": round(similarity, 4),
            }
        )

    return chunks


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How do I return an item?"
    print(f"\nQuery: {query}\n")
    chunks = retrieve(query, top_k=DEFAULT_TOP_K)
    for i, chunk in enumerate(chunks, 1):
        print(f"[{i}] {chunk['doc_name']} (score: {chunk['similarity_score']:.4f})")
        print(f"    {chunk['text'][:200]}...\n")
