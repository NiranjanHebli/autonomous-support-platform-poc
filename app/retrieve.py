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
import json
from sentence_transformers import CrossEncoder
from core.llm_core import generate_completion
from core.prompts import REWRITE_PROMPT

# Load cross-encoder once
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


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


def rewrite_query(query: str) -> list[str]:
    """Generate variations of the query for higher recall."""
    prompt = REWRITE_PROMPT.format(query=query)
    res = generate_completion(
        system_prompt="You are a JSON-only query expansion assistant.",
        user_message=prompt,
        max_tokens=200,
        temperature=0.7,
    )
    raw_text = res["answer"].strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.startswith("```"):
        raw_text = raw_text[3:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
        queries = parsed.get("queries", [])
        if query not in queries:
            queries.append(query)
        return queries
    except Exception:
        return [query]


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Query ChromaDB and BM25 using multi-query expansion, combine with RRF,
    and finally re-rank the top candidates using a Cross-Encoder.
    """
    collection = get_collection()
    num_total = collection.count()
    if num_total == 0:
        return []

    # 1. Query Expansion
    queries = rewrite_query(query)

    # Get all chunks and their semantic distances for ALL queries
    semantic_results = collection.query(
        query_texts=queries,
        n_results=num_total,
        include=["documents", "metadatas", "distances"],
    )

    ids_0 = semantic_results["ids"][0]
    docs_0 = semantic_results["documents"][0]
    metas_0 = semantic_results["metadatas"][0]

    # Pool semantic scores by taking the minimum distance across all query variations
    chunk_min_dist = {chunk_id: float("inf") for chunk_id in ids_0}
    for q_idx in range(len(queries)):
        for i, chunk_id in enumerate(semantic_results["ids"][q_idx]):
            dist = semantic_results["distances"][q_idx][i]
            if dist < chunk_min_dist[chunk_id]:
                chunk_min_dist[chunk_id] = dist

    semantic_ids = sorted(ids_0, key=lambda cid: chunk_min_dist[cid])
    semantic_ranks = {chunk_id: rank for rank, chunk_id in enumerate(semantic_ids)}

    # 2. BM25 ranks
    from rank_bm25 import BM25Okapi

    tokenized_corpus = [doc.lower().split() for doc in docs_0]
    bm25 = BM25Okapi(tokenized_corpus)

    # Pool BM25 scores by taking the max score across all query variations
    chunk_max_bm25 = {chunk_id: 0.0 for chunk_id in ids_0}
    for q in queries:
        scores = bm25.get_scores(q.lower().split())
        for chunk_id, score in zip(ids_0, scores):
            if score > chunk_max_bm25[chunk_id]:
                chunk_max_bm25[chunk_id] = score

    bm25_scores_with_ids = list(chunk_max_bm25.items())
    bm25_scores_sorted = sorted(bm25_scores_with_ids, key=lambda x: x[1], reverse=True)
    bm25_ranks = {
        chunk_id: rank for rank, (chunk_id, _) in enumerate(bm25_scores_sorted)
    }

    # 3. Combine with RRF
    combined_scores = {}
    for chunk_id in ids_0:
        s_rank = semantic_ranks[chunk_id]
        b_rank = bm25_ranks[chunk_id]
        combined_scores[chunk_id] = (1.0 / (60 + s_rank)) + (1.0 / (60 + b_rank))

    # Sort combined
    sorted_combined = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

    # 4. CROSS-ENCODER RE-RANKING
    top_k_rerank = min(top_k * 3, num_total)
    candidate_ids = [x[0] for x in sorted_combined[:top_k_rerank]]

    chunk_lookup = {
        ids_0[i]: {
            "text": docs_0[i],
            "doc_name": metas_0[i].get("doc_name", "unknown"),
        }
        for i in range(num_total)
    }

    pairs = [[query, chunk_lookup[cid]["text"]] for cid in candidate_ids]
    ce_scores = cross_encoder.predict(pairs)

    candidate_chunks = []
    for cid, ce_score in zip(candidate_ids, ce_scores):
        info = chunk_lookup[cid]
        candidate_chunks.append(
            {
                "chunk_id": cid,
                "doc_name": info["doc_name"],
                "text": info["text"],
                "similarity_score": round(float(ce_score), 4),
            }
        )

    candidate_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)

    return candidate_chunks[:top_k]


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How do I return an item?"
    print(f"\nQuery: {query}\n")
    chunks = retrieve(query, top_k=DEFAULT_TOP_K)
    for i, chunk in enumerate(chunks, 1):
        print(f"[{i}] {chunk['doc_name']} (score: {chunk['similarity_score']:.4f})")
        print(f"    {chunk['text']}\n")
