"""
Experiment 2: Reduce chunk max_words from 200 -> 100.

Hypothesis: Smaller, more focused chunks improve Context Precision
(the relevant content is not diluted by surrounding text),
at the possible cost of Context Recall (an answer spanning multiple
sentences might get split across two chunks).

This experiment re-ingests the corpus with the smaller chunk size
into a SEPARATE ChromaDB collection to avoid overwriting the baseline.

Uses: Ollama LLM + local sentence-transformers embeddings

Usage:
    uv run python experiments/exp2_chunk_size.py
"""

import csv
import re
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.generate import generate
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.run_config import RunConfig
from datasets import Dataset

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rich.console import Console

from core.config import POLICIES_DIR, CHROMA_DIR, GOLDEN_SET_PATH, EMBEDDING_MODEL
from core.llm_core import get_ragas_llm, get_ragas_embeddings

console = Console()

EXP_COLLECTION = "cartly_policies_exp2_chunk100"

# Experiment: smaller chunks
CHUNK_MIN_WORDS = 30
CHUNK_MAX_WORDS = 100  # changed from baseline 200


def chunk_recursive_semantic(text: str, doc_name: str) -> list[dict]:
    chunks, chunk_idx = [], 0
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    current_words: list[str] = []

    def flush():
        nonlocal chunk_idx
        if current_words:
            chunks.append(
                {
                    "chunk_id": f"{doc_name}_chunk_{chunk_idx:03d}",
                    "doc_name": doc_name,
                    "text": " ".join(current_words),
                }
            )
            chunk_idx += 1

    for para in paragraphs:
        para_words = para.split()
        if len(para_words) > CHUNK_MAX_WORDS:
            for sent in re.split(r"(?<=[.!?])\s+", para):
                sent_words = sent.split()
                if len(current_words) + len(sent_words) > CHUNK_MAX_WORDS:
                    flush()
                    current_words = sent_words
                else:
                    current_words.extend(sent_words)
        else:
            if len(current_words) + len(para_words) > CHUNK_MAX_WORDS:
                flush()
                current_words = para_words
            else:
                current_words.extend(para_words)
            if len(current_words) >= CHUNK_MIN_WORDS:
                flush()
                current_words = []

    flush()
    return chunks


def ingest_experiment_collection():
    """Build and ingest the smaller-chunk collection."""
    console.print(f"[dim]Building experiment collection: {EXP_COLLECTION}[/dim]")
    all_chunks = []
    for md_file in sorted(POLICIES_DIR.glob("*.md")):
        text = md_file.read_text(encoding="utf-8").strip()
        all_chunks.extend(chunk_recursive_semantic(text, md_file.stem))

    console.print(
        f"Generated [bold]{len(all_chunks)}[/bold] chunks (max_words={CHUNK_MAX_WORDS})."
    )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

    try:
        client.delete_collection(EXP_COLLECTION)
    except Exception:
        pass

    collection = client.create_collection(
        name=EXP_COLLECTION,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    batch_size = 50
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        collection.add(
            ids=[c["chunk_id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{"doc_name": c["doc_name"]} for c in batch],
        )

    console.print("[green]Experiment collection ingested.[/green]")
    return collection


def retrieve_exp(collection, query: str, top_k: int = 3) -> list[dict]:
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for cid, text, meta, dist in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append(
            {
                "chunk_id": cid,
                "doc_name": meta.get("doc_name", ""),
                "text": text,
                "similarity_score": round(1.0 - dist / 2.0, 4),
            }
        )
    return chunks


def main():
    console.rule("[bold]Experiment 2: chunk max_words = 100[/bold]")
    console.print("Using local sentence-transformers for embeddings.\n")

    collection = ingest_experiment_collection()

    rows = []
    with open(GOLDEN_SET_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    for i, row in enumerate(rows, 1):
        console.print(f"[dim][{i:02d}/{len(rows)}] {row['question']}[/dim]")
        try:
            chunks = retrieve_exp(collection, row["question"], top_k=3)
            gen = generate(row["question"], chunks)
            results.append(
                {
                    "question": row["question"],
                    "answer": gen["answer"],
                    "contexts": [c["text"] for c in chunks],
                    "ground_truth": row["ground_truth_answer"],
                }
            )
        except Exception as e:
            console.print(f"  [red]ERROR:[/red] {e}")
        time.sleep(0.3)

    # Configure Ragas with centralized LLM and embeddings
    ragas_llm = get_ragas_llm()
    ragas_embeddings = get_ragas_embeddings()

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    for metric in metrics:
        metric.llm = ragas_llm
        if hasattr(metric, "embeddings"):
            metric.embeddings = ragas_embeddings

    dataset = Dataset.from_list([r for r in results if r["answer"] != "ERROR"])
    console.print("\n[bold]Scoring with Ragas (Ollama, parallel)...[/bold]")
    run_config = RunConfig(max_workers=16, timeout=120)
    evaluation_result = evaluate(dataset, metrics=metrics, run_config=run_config)

    # Extract mean scores into a plain dict via to_pandas() to avoid
    # EvaluationResult API inconsistencies across Ragas versions.
    try:
        df = evaluation_result.to_pandas()
        metric_cols = [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
        ]
        scores = {
            col: float(df[col].mean()) for col in metric_cols if col in df.columns
        }
    except Exception as e:
        console.print(f"[yellow]Warning: score extraction failed ({e})[/yellow]")
        scores = {}

    console.print(
        "\n[bold cyan]Experiment 2 Results (chunk_max_words=100):[/bold cyan]"
    )
    for metric in [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]:
        val = scores.get(metric, "N/A")
        console.print(
            f"  {metric}: {val:.3f}" if isinstance(val, float) else f"  {metric}: {val}"
        )

    console.print(f"\nUpdate [bold]experiments/RESULTS.md[/bold] with these numbers.")


if __name__ == "__main__":
    main()
