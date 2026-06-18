"""
Experiment 1: Change top_k from 3 -> 5.

Hypothesis: Retrieving more chunks gives the LLM more context,
which should improve Context Recall and Answer Relevancy,
at the risk of slightly lower Context Precision (more noise).

Uses: Ollama LLM + local sentence-transformers embeddings (same as baseline)

Usage:
    uv run python experiments/exp1_top_k.py
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

EXPERIMENT_TOP_K = 5  # changed from baseline of 3


def main():
    console.rule("[bold]Experiment 1: top_k = 5[/bold]")
    console.print(
        f"Baseline top_k: 3  ->  Experiment top_k: [bold]{EXPERIMENT_TOP_K}[/bold]\n"
    )

    rows = []
    with open(GOLDEN_SET_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    for i, row in enumerate(rows, 1):
        console.print(f"[dim][{i:02d}/{len(rows)}] {row['question']}[/dim]")
        try:
            output = run(row["question"], top_k=EXPERIMENT_TOP_K)
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

    console.print("\n[bold cyan]Experiment 1 Results (top_k=5):[/bold cyan]")
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
