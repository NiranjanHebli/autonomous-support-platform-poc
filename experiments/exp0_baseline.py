"""
Experiment 0: Baseline Evaluation

Runs the RAG pipeline using the original baseline configuration:
- top_k = 3

Note: Chunking strategy and system prompt will reflect whatever
is currently in production (core/config.py and core/prompts.py).
To run a true historical baseline, ensure CHUNK_MAX_WORDS=200
and the standard SYSTEM_PROMPT are active.

Usage:
    uv run python experiments/exp0_baseline.py
"""

import csv
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.pipeline import run
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from ragas.run_config import RunConfig
from datasets import Dataset

from rich.console import Console

from core.config import GOLDEN_SET_PATH
from core.llm_core import get_ragas_llm, get_ragas_embeddings

console = Console()

BASELINE_TOP_K = 3


def main():
    console.rule("[bold]Baseline Test: top_k = 3[/bold]")
    console.print(f"Running baseline with top_k: [bold]{BASELINE_TOP_K}[/bold]\n")

    rows = []
    with open(GOLDEN_SET_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    for i, row in enumerate(rows, 1):
        console.print(f"[dim][{i:02d}/{len(rows)}] {row['question']}[/dim]")
        try:
            output = run(row["question"], top_k=BASELINE_TOP_K)
            results.append(
                {
                    "question": row["question"],
                    "answer": output["answer"],
                    "contexts": output["contexts"],
                    "ground_truth": row["ground_truth_answer"],
                }
            )
        except Exception as e:
            console.print(f"  [red]ERROR:[/red] {e}")
        time.sleep(0.3)

    if not results:
        console.print("[red]No results to evaluate.[/red]")
        return

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
    run_config = RunConfig(max_workers=2, timeout=600, max_retries=10)
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

    console.print("\n[bold cyan]Baseline Results (top_k=3):[/bold cyan]")
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
