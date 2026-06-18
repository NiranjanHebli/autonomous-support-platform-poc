"""
Ingests all Cartly policy documents from /data/policies/, treats each
document as a single chunk with a topic prefix derived from the filename,
embeds them with sentence-transformers (all-MiniLM-L6-v2 — local, free,
no API key), and persists them into ChromaDB.

Strategy rationale:
  - All 27 policy docs are 28–179 words — small enough to be a single chunk.
  - Prepending "Topic: <name>" adds a strong semantic anchor that improves
    cosine-similarity matching for user questions.
  - No information is lost at chunk boundaries.

Usage:
    uv run python app/ingest.py

This only needs to be run once (or whenever /data/policies/ changes).
"""

import re
import sys
from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rich.console import Console
from rich.progress import track

# Ensure project root is on the path so `core` is importable when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import (
    POLICIES_DIR,
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)

console = Console()

# ---------------------------------------------------------------------------
# Chunking — Whole-Document with Topic Prefix
# ---------------------------------------------------------------------------


def _topic_from_filename(filename_stem: str) -> str:
    """
    Convert a snake_case filename stem into a human-readable topic label.
    e.g. 'get_refund' → 'Get Refund', 'check_payment_methods' → 'Check Payment Methods'
    """
    return filename_stem.replace("_", " ").title()


def chunk_whole_document(text: str, doc_name: str) -> list[dict]:
    """
    Treat the entire document as a single chunk, prepended with a
    topic label derived from the filename for improved embedding similarity.

    Returns a list with exactly one chunk dict.
    """
    topic = _topic_from_filename(doc_name)

    # Strip the markdown title line (e.g. "# Get Refund\n\n") since we're
    # adding our own topic prefix — avoids redundancy in the embedding.
    body = re.sub(r"^#\s+.*?\n+", "", text, count=1).strip()

    chunk_text = f"Topic: {topic}. {body}"

    return [
        {
            "chunk_id": f"{doc_name}_full",
            "doc_name": doc_name,
            "text": chunk_text,
        }
    ]


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------


def ingest():
    console.rule("[bold blue]Cartly Policy Ingestion[/bold blue]")
    console.print(
        f"[dim]Embedding model: {EMBEDDING_MODEL} (local, no API key required)[/dim]"
    )
    console.print("[dim]Strategy: whole-document-as-chunk with topic prefix[/dim]\n")

    # Load policy documents
    policy_files = sorted(POLICIES_DIR.glob("*.md"))
    if not policy_files:
        console.print(f"[red]No .md files found in {POLICIES_DIR}[/red]")
        raise SystemExit(1)

    console.print(f"Found [bold]{len(policy_files)}[/bold] policy documents.")

    # Build all chunks (1 per document)
    all_chunks: list[dict] = []
    for md_file in policy_files:
        text = md_file.read_text(encoding="utf-8").strip()
        doc_name = md_file.stem
        chunks = chunk_whole_document(text, doc_name)
        all_chunks.extend(chunks)

    console.print(
        f"Generated [bold]{len(all_chunks)}[/bold] chunks (1 per document).\n"
    )

    # Set up ChromaDB with local sentence-transformer embeddings
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)

    # Delete existing collection so re-runs are idempotent
    try:
        client.delete_collection(COLLECTION_NAME)
        console.print("[dim]Deleted existing collection for fresh ingest.[/dim]")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Upsert all chunks (27 docs fits in a single batch)
    for i in track(range(0, len(all_chunks), 50), description="Embedding & storing..."):
        batch = all_chunks[i : i + 50]
        collection.add(
            ids=[c["chunk_id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{"doc_name": c["doc_name"]} for c in batch],
        )

    console.print(
        f"\n[green]✓ Ingestion complete.[/green] {len(all_chunks)} chunks stored in ChromaDB at [dim]{CHROMA_DIR}[/dim]"
    )


if __name__ == "__main__":
    ingest()
