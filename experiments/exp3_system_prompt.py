"""
Experiment 3: Tighten the system prompt to demand sentence-level citations.

Hypothesis: Requiring the model to cite the exact supporting sentence
(rather than just the document name) forces it to stay strictly grounded,
improving Faithfulness at the possible cost of slight verbosity.

Uses: Ollama LLM (llama3.1:8b) + local sentence-transformers embeddings

Usage:
    uv run python experiments/exp3_system_prompt.py
"""

import csv
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.retrieve import retrieve
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
from core.llm_core import generate_completion, get_ragas_llm, get_ragas_embeddings
from core.prompts import TIGHTENED_SYSTEM_PROMPT, CONTEXT_TEMPLATE, USER_TEMPLATE

console = Console()


def generate_tightened(query: str, chunks: list[dict]) -> dict:
    context_parts = [
        CONTEXT_TEMPLATE.format(
            i=i + 1, doc_name=c["doc_name"], chunk_id=c["chunk_id"], text=c["text"]
        )
        for i, c in enumerate(chunks)
    ]
    context_block = "\n\n".join(context_parts)
    user_message = USER_TEMPLATE.format(context_block=context_block, query=query)

    result = generate_completion(
        system_prompt=TIGHTENED_SYSTEM_PROMPT,
        user_message=user_message,
        max_tokens=450,
        temperature=0.2,
    )

    return {
        "answer": result["answer"],
        "cited_chunks": [c["chunk_id"] for c in chunks],
    }


def main():
    console.rule("[bold]Experiment 3: Tightened Citation System Prompt[/bold]")
    console.print(
        "Change: require exact sentence-level quote instead of document name.\n"
    )

    rows = []
    with open(GOLDEN_SET_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    results = []
    for i, row in enumerate(rows, 1):
        console.print(f"[dim][{i:02d}/{len(rows)}] {row['question']}[/dim]")
        try:
            chunks = retrieve(row["question"], top_k=DEFAULT_TOP_K)
            gen = generate_tightened(row["question"], chunks)
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
        "\n[bold cyan]Experiment 3 Results (tightened citation prompt):[/bold cyan]"
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
