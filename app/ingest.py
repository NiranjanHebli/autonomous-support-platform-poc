"""
Ingests all Cartly policy documents from /data/policies/, splits each
document into semantic paragraph-level chunks with a topic prefix,
embeds them with sentence-transformers (all-MiniLM-L6-v2 -- local, free,
no API key), and persists them into ChromaDB.

Strategy rationale:
  - Policy docs are 28-179 words. Whole-doc chunking dilutes the embedding
    signal with conversational filler, hurting precision.
  - Splitting on paragraph boundaries preserves logical units of meaning.
  - Merging very short paragraphs (< CHUNK_MIN_WORDS) avoids fragments.
  - Prepending "Topic: <name>" adds a strong semantic anchor that improves
    cosine-similarity matching for user questions.

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
    CHUNK_MIN_WORDS,
    CHUNK_MAX_WORDS,
)

console = Console()

# ---------------------------------------------------------------------------
# Chunking -- Semantic Paragraph with Topic Prefix
# ---------------------------------------------------------------------------


def _topic_from_filename(filename_stem: str) -> str:
    """
    Convert a snake_case filename stem into a human-readable topic label.
    e.g. 'get_refund' -> 'Get Refund', 'check_payment_methods' -> 'Check Payment Methods'
    """
    return filename_stem.replace("_", " ").title()


def chunk_semantic_paragraphs(text: str, doc_name: str) -> list[dict]:
    """
    Split a document into semantic paragraph-level chunks.

    1. Strip the markdown title (we add our own topic prefix).
    2. Split on double-newlines (paragraph boundaries).
    3. Merge short paragraphs (< CHUNK_MIN_WORDS) with the next.
    4. Cap each chunk at CHUNK_MAX_WORDS; if a paragraph exceeds it,
       split by sentences.
    5. Prepend 'Topic: <name>.' to each chunk for embedding quality.

    Returns a list of chunk dicts.
    """
    topic = _topic_from_filename(doc_name)

    # Strip the markdown title line (e.g. "# Get Refund\n\n") since we're
    # adding our own topic prefix -- avoids redundancy in the embedding.
    body = re.sub(r"^#\s+.*?\n+", "", text, count=1).strip()

    # Split into paragraphs
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]

    # If no paragraph breaks, treat as a single paragraph
    if not paragraphs:
        paragraphs = [body]

    chunks = []
    chunk_idx = 0
    current_words: list[str] = []

    def flush():
        nonlocal chunk_idx
        if current_words:
            chunk_text = f"Topic: {topic}. " + " ".join(current_words)
            chunks.append(
                {
                    "chunk_id": f"{doc_name}_chunk_{chunk_idx:03d}",
                    "doc_name": doc_name,
                    "text": chunk_text,
                }
            )
            chunk_idx += 1

    for para in paragraphs:
        para_words = para.split()

        # If paragraph itself exceeds max_words, split by sentences
        if len(para_words) > CHUNK_MAX_WORDS:
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sentence in sentences:
                sent_words = sentence.split()
                if len(current_words) + len(sent_words) > CHUNK_MAX_WORDS:
                    flush()
                    current_words = sent_words
                else:
                    current_words.extend(sent_words)
        else:
            # Try to merge with current accumulator
            if len(current_words) + len(para_words) > CHUNK_MAX_WORDS:
                flush()
                current_words = para_words
            else:
                current_words.extend(para_words)

            # Flush if we've hit the minimum meaningful chunk size
            if len(current_words) >= CHUNK_MIN_WORDS:
                flush()
                current_words = []

    flush()  # flush any remaining words
    return chunks


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------


def ingest():
    console.rule("[bold blue]Cartly Policy Ingestion[/bold blue]")
    console.print(
        f"[dim]Embedding model: {EMBEDDING_MODEL} (local, no API key required)[/dim]"
    )
    console.print(
        "[dim]Strategy: semantic paragraph chunking with topic prefix[/dim]\n"
    )

    # Load policy documents
    policy_files = sorted(POLICIES_DIR.glob("*.md"))
    if not policy_files:
        console.print(f"[red]No .md files found in {POLICIES_DIR}[/red]")
        raise SystemExit(1)

    console.print(f"Found [bold]{len(policy_files)}[/bold] policy documents.")

    # Build all chunks
    all_chunks: list[dict] = []
    for md_file in policy_files:
        text = md_file.read_text(encoding="utf-8").strip()
        doc_name = md_file.stem
        chunks = chunk_semantic_paragraphs(text, doc_name)
        all_chunks.extend(chunks)

    console.print(
        f"Generated [bold]{len(all_chunks)}[/bold] chunks from {len(policy_files)} documents.\n"
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

    # Upsert all chunks
    for i in track(range(0, len(all_chunks), 50), description="Embedding & storing..."):
        batch = all_chunks[i : i + 50]
        collection.add(
            ids=[c["chunk_id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[{"doc_name": c["doc_name"]} for c in batch],
        )

    console.print(
        f"\n[green] Ingestion complete.[/green] {len(all_chunks)} chunks stored in ChromaDB at [dim]{CHROMA_DIR}[/dim]"
    )


if __name__ == "__main__":
    ingest()
