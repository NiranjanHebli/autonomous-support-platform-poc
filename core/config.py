"""
Centralized application configurations, static variables, and settings.
Contains no business logic.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Directories & Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent.parent
POLICIES_DIR = ROOT_DIR / "data" / "policies"
CHROMA_DIR = ROOT_DIR / "data" / "chroma_store"

# Evaluation Paths
GOLDEN_SET_PATH = ROOT_DIR / "eval" / "golden_set.csv"
RESULTS_CSV_PATH = ROOT_DIR / "eval" / "results.csv"
SCORECARD_PATH = ROOT_DIR / "eval" / "scorecard.md"

# ---------------------------------------------------------------------------
# RAG Configuration
# ---------------------------------------------------------------------------
COLLECTION_NAME = "cartly_policies"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OLLAMA_MODEL = "llama3.1:8b"

# Chunking strategy: semantic paragraph chunking with topic prefix
CHUNK_MIN_WORDS = 30
CHUNK_MAX_WORDS = 150

# Retrieval Defaults
DEFAULT_TOP_K = 5

# ---------------------------------------------------------------------------
# Evaluation Targets
# ---------------------------------------------------------------------------
# PRD targets from docs/PRD.md and TECHNICAL_DESIGN.md
PRD_TARGETS = {
    "faithfulness": 0.90,
    "answer_relevancy": 0.85,
    "context_precision": 0.80,
    "context_recall": 0.85,
}

PASS_FLOORS = {
    "faithfulness": 0.80,
    "answer_relevancy": 0.80,
    "context_precision": 0.70,
    "context_recall": 0.80,
}
