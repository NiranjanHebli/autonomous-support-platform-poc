"""
Test Experiment: Runs only the first 5 questions to quickly test Ragas evaluation.

Usage:
    uv run python experiments/exp_test_5.py
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

from core.config import GOLDEN_SET_PATH, DEFAULT_TOP_K
from core.llm_core import get_ragas_llm, get_ragas_embeddings

console = Console()


def main():
    console.rule("[bold]Test: First 5 Questions[/bold]")

    rows = []
    with open(GOLDEN_SET_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Take only the first 5 rows
    rows = rows[:5]
    console.print(f"Running test on [bold]{len(rows)}[/bold] questions.\n")

    results = []
    for i, row in enumerate(rows, 1):
        console.print(f"[dim][{i:02d}/{len(rows)}] {row['question']}[/dim]")
        try:
            output = run(row["question"], top_k=DEFAULT_TOP_K)
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
    console.print("\n[bold]Scoring with Ragas (Ollama)...[/bold]")

    # Reduced workers, increased timeout and retries for local Ollama to avoid timeout errors
    run_config = RunConfig(max_workers=2, timeout=600, max_retries=10)

    evaluation_result = evaluate(dataset, metrics=metrics, run_config=run_config)

    # Extract mean scores
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

    console.print("\n[bold cyan]Test Results (5 questions):[/bold cyan]")
    for metric in [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]:
        val = scores.get(metric, "N/A")
        if isinstance(val, float):
            console.print(f"  {metric}: {val:.3f}")
        else:
            console.print(f"  {metric}: {val}")


if __name__ == "__main__":
    main()
