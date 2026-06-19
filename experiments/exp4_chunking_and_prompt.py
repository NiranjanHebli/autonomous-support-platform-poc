"""
Experiment 4: Semantic paragraph chunking + improved system prompt.

Hypothesis: Splitting documents into focused paragraph-level chunks (instead
of whole-document-as-chunk) reduces embedding dilution, improving Context
Precision. The updated system prompt with multi-chunk synthesis instructions
improves Answer Relevancy and Context Recall.

Uses: Ollama LLM (llama3.1:8b) + local sentence-transformers embeddings

Usage:
    uv run python experiments/exp4_chunking_and_prompt.py
"""

import csv
import re
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.retrieve import retrieve
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

from rich.console import Console
from rich.table import Table
from rich import box

from core.config import GOLDEN_SET_PATH, DEFAULT_TOP_K
from core.llm_core import get_ragas_llm, get_ragas_embeddings

console = Console()

# ---------------------------------------------------------------------------
# 5 questions selected to cover all categories:
#   1 easy, 1 easy, 1 ambiguous, 1 multi-hop, 1 adversarial
# ---------------------------------------------------------------------------
SELECTED_QUESTIONS = [
    "How do I return an item?",
    "What payment methods does Cartly accept?",
    "I want to return an item but it's been over 30 days. Am I still eligible?",
    "I want to return a damaged item AND track the refund once approved. Walk me through the full process.",
    "What is Cartly's stock price on the NASDAQ?",
]


def main():
    console.rule(
        "[bold]Experiment 4: Semantic Paragraph Chunking + Improved Prompt[/bold]"
    )
    console.print("Changes: paragraph-level chunking + multi-chunk synthesis prompt\n")

    # Load full golden set, filter to selected questions
    rows = []
    with open(GOLDEN_SET_PATH, newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
        for row in all_rows:
            if row["question"] in SELECTED_QUESTIONS:
                rows.append(row)

    console.print(f"Running on [bold]{len(rows)}[/bold] selected questions.\n")

    results = []
    for i, row in enumerate(rows, 1):
        console.print(f"[dim][{i:02d}/{len(rows)}] {row['question']}[/dim]")
        try:
            # Use the production pipeline (which now uses semantic paragraph chunks)
            chunks = retrieve(row["question"], top_k=DEFAULT_TOP_K)
            gen = generate(row["question"], chunks)
            results.append(
                {
                    "question": row["question"],
                    "answer": gen["answer"],
                    "contexts": [c["text"] for c in chunks],
                    "ground_truth": row["ground_truth_answer"],
                }
            )
            console.print(f"  [green]OK[/green] ({len(chunks)} chunks retrieved)")
        except Exception as e:
            console.print(f"  [red]ERROR:[/red] {e}")
        time.sleep(0.5)

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
    console.print("\n[bold]Scoring with Ragas (Ollama, sequential)...[/bold]")
    run_config = RunConfig(max_workers=1, timeout=240)
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

    # Print results comparison table
    baseline = {
        "faithfulness": 0.778,
        "answer_relevancy": 0.535,
        "context_precision": 0.250,
        "context_recall": 0.167,
    }

    console.print()
    table = Table(
        title="Experiment 4 Results vs. Baseline",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Metric", style="bold")
    table.add_column("Baseline", justify="right")
    table.add_column("Exp 4", justify="right")
    table.add_column("Delta", justify="right")

    for metric_name in metric_cols:
        base_val = baseline.get(metric_name, 0.0)
        exp_val = scores.get(metric_name, 0.0)
        delta = exp_val - base_val
        delta_str = f"{delta:+.3f}"
        if delta > 0:
            delta_str = f"[green]{delta_str}[/green]"
        elif delta < 0:
            delta_str = f"[red]{delta_str}[/red]"

        table.add_row(
            metric_name,
            f"{base_val:.3f}",
            f"{exp_val:.3f}",
            delta_str,
        )

    console.print(table)

    # Also print per-question breakdown
    if "df" in dir() or "df" in locals():
        console.print("\n[bold]Per-Question Breakdown:[/bold]")
        for idx, row_data in df.iterrows():
            q = row_data.get("question", f"Q{idx+1}")
            console.print(f"\n  [dim]{q}[/dim]")
            for m in metric_cols:
                val = row_data.get(m, "N/A")
                if isinstance(val, float):
                    console.print(f"    {m}: {val:.3f}")

    console.print(f"\nUpdate [bold]experiments/RESULTS.md[/bold] with these numbers.")


if __name__ == "__main__":
    main()
