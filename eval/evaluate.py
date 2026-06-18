"""
Runs all 50 questions from the golden eval set through the RAG pipeline
and scores them using Ragas metrics:
  - Faithfulness         (no hallucinations vs retrieved context)
  - Answer Relevancy     (does the answer address the question?)
  - Context Precision    (are the right chunks ranked highest?)
  - Context Recall       (does the retrieved context cover the ground truth?)

LLM for Ragas evaluation: centralized via core.llm_core
Embeddings for Ragas evaluation: centralized via core.llm_core

Usage:
    uv run python eval/evaluate.py

Outputs:
    eval/scorecard.md  — human-readable baseline scorecard
    eval/results.csv   — per-question scores for error analysis
"""

import csv
import time
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Ensure the root directory is in the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Monkeypatch for ragas 0.3.1 bug with langchain-community 0.4.x
if "langchain_community.chat_models.vertexai" not in sys.modules:
    sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()

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
from rich.table import Table
from rich import box

from core.config import (
    GOLDEN_SET_PATH,
    RESULTS_CSV_PATH,
    SCORECARD_PATH,
    PRD_TARGETS,
    PASS_FLOORS,
    DEFAULT_TOP_K,
)
from core.llm_core import get_ragas_llm, get_ragas_embeddings

console = Console()


def load_golden_set() -> list[dict]:
    rows = []
    with open(GOLDEN_SET_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def run_pipeline_on_golden_set(golden_rows: list[dict]) -> list[dict]:
    """Run each question through the RAG pipeline and collect outputs."""

    results = []
    console.print(
        f"\nRunning [bold]{len(golden_rows)}[/bold] questions through the RAG pipeline...\n"
    )

    for i, row in enumerate(golden_rows, 1):
        question = row["question"]
        ground_truth = row["ground_truth_answer"]
        category = row["category"]

        console.print(f"[dim][{i:02d}/{len(golden_rows)}] {question[:70]}...[/dim]")

        try:
            output = run(question, top_k=DEFAULT_TOP_K)
            results.append(
                {
                    "question": question,
                    "answer": output["answer"],
                    "contexts": output["contexts"],
                    "ground_truth": ground_truth,
                    "category": category,
                    "retrieved_docs": ", ".join(
                        c["doc_name"] for c in output["retrieved_chunks"]
                    ),
                }
            )
        except Exception as e:
            console.print(f"  [red]ERROR:[/red] {e}")
            results.append(
                {
                    "question": question,
                    "answer": "ERROR",
                    "contexts": [],
                    "ground_truth": ground_truth,
                    "category": category,
                    "retrieved_docs": "",
                }
            )

        # Small delay to avoid Ollama execution time
        time.sleep(0.3)

    return results


def extract_scores(evaluation_result) -> dict:
    """Convert a Ragas EvaluationResult into a plain {metric: mean_score} dict."""
    try:
        df = evaluation_result.to_pandas()
        metric_cols = [
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
        ]
        return {col: float(df[col].mean()) for col in metric_cols if col in df.columns}
    except Exception as e:
        console.print(
            f"[yellow]Warning: could not extract scores from Ragas result ({e})[/yellow]"
        )
        # Fall back to _repr_dict if available
        if hasattr(evaluation_result, "_repr_dict"):
            return dict(evaluation_result._repr_dict)
        return {}


def score_with_ragas(results: list[dict]) -> dict:
    """Compute Ragas metrics across all results using centralized LLM and embeddings."""

    ragas_llm = get_ragas_llm()
    ragas_embeddings = get_ragas_embeddings()

    # Inject LLM + embeddings into each metric
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    for metric in metrics:
        metric.llm = ragas_llm
        if hasattr(metric, "embeddings"):
            metric.embeddings = ragas_embeddings

    dataset = Dataset.from_list(
        [
            {
                "question": r["question"],
                "answer": r["answer"],
                "contexts": (
                    r["contexts"]
                    if isinstance(r["contexts"], list)
                    else [r["contexts"]]
                ),
                "ground_truth": r["ground_truth"],
            }
            for r in results
            if r["answer"] != "ERROR"
        ]
    )

    console.print("\n[bold]Running Ragas evaluation (parallel)...[/bold]")
    run_config = RunConfig(max_workers=2, timeout=600, max_retries=10)
    evaluation_result = evaluate(dataset, metrics=metrics, run_config=run_config)

    # Convert EvaluationResult to plain dict of means so all downstream
    # functions can use simple .get() calls without worrying about the
    # EvaluationResult API changing between Ragas versions.
    scores = extract_scores(evaluation_result)
    console.print(f"[dim]Scores extracted: {scores}[/dim]")
    return scores, evaluation_result


def save_results_csv(results: list[dict], evaluation_result):
    """Save per-question scores to CSV for error analysis."""
    if evaluation_result is not None and hasattr(evaluation_result, "to_pandas"):
        try:
            df = evaluation_result.to_pandas()
            df.to_csv(RESULTS_CSV_PATH, index=False)
            console.print(
                f"[dim]Per-question results saved to {RESULTS_CSV_PATH}[/dim]"
            )
        except Exception as e:
            console.print(f"[yellow]Warning: could not save results CSV ({e})[/yellow]")


def write_scorecard(scores: dict):
    """Write the baseline scorecard markdown file."""
    lines = [
        "# Cartly Support Copilot — Baseline Ragas Scorecard",
        "",
        "**LLM:** Local Ollama llama3.1:8b",
        "**Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (local)",
        "**Vector Store:** ChromaDB (cosine, top-k=5)",
        "**Golden Set:** 50 Q&A pairs (20 easy, 10 ambiguous, 10 multi-hop, 10 adversarial)",
        "",
        "---",
        "",
        "## Results vs. Week 15 PRD Targets",
        "",
        "| Metric | Actual | PRD Target | Pass Floor | Status |",
        "|---|---|---|---|---|",
    ]

    for metric, target in PRD_TARGETS.items():
        actual = scores.get(metric, 0.0)
        if isinstance(actual, float):
            actual_str = f"{actual:.3f}"
        else:
            actual_str = str(actual)
        floor = PASS_FLOORS[metric]
        try:
            actual_f = float(actual)
            if actual_f >= target:
                status = "PASS (target met)"
            elif actual_f >= floor:
                status = "MARGINAL (above floor)"
            else:
                status = "FAIL (below floor)"
        except (ValueError, TypeError):
            status = "N/A"
        lines.append(
            f"| {metric.replace('_', ' ').title()} | {actual_str} | >= {target} | >= {floor} | {status} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Notes",
        "",
        "- Adversarial queries should produce 'I cannot answer' responses.",
        "  Faithfulness on these rows will be high if the model correctly abstains.",
        "- See `eval/results.csv` for per-question breakdown.",
        "- See `experiments/RESULTS.md` for improvement experiments.",
    ]

    SCORECARD_PATH.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"\n[green]Scorecard written to {SCORECARD_PATH}[/green]")


def print_scorecard_table(scores: dict):
    """Print the scorecard as a rich table in the terminal."""
    table = Table(
        title="Cartly RAG Pipeline — Ragas Baseline Scorecard",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Metric", style="bold")
    table.add_column("Actual", justify="center")
    table.add_column("PRD Target", justify="center")
    table.add_column("Status", justify="center")

    for metric, target in PRD_TARGETS.items():
        actual = scores.get(metric, 0.0)
        try:
            actual_f = float(actual)
            actual_str = f"{actual_f:.3f}"
            floor = PASS_FLOORS[metric]
            if actual_f >= target:
                status = "[green]PASS[/green]"
            elif actual_f >= floor:
                status = "[yellow]MARGINAL[/yellow]"
            else:
                status = "[red]FAIL[/red]"
        except (ValueError, TypeError):
            actual_str = str(actual)
            status = "N/A"

        table.add_row(
            metric.replace("_", " ").title(),
            actual_str,
            f">= {target}",
            status,
        )

    console.print()
    console.print(table)


def main():
    console.rule("[bold blue]Cartly RAG — Evaluation Harness[/bold blue]")

    golden_rows = load_golden_set()
    console.print(f"Loaded [bold]{len(golden_rows)}[/bold] rows from golden set.")

    results = run_pipeline_on_golden_set(golden_rows)

    scores, evaluation_result = score_with_ragas(results)

    print_scorecard_table(scores)
    write_scorecard(scores)
    save_results_csv(results, evaluation_result)

    console.print("\n[bold green]Evaluation complete![/bold green]")
    console.print(f"  Scorecard -> {SCORECARD_PATH}")
    console.print(f"  Per-question results -> {RESULTS_CSV_PATH}")


if __name__ == "__main__":
    main()
