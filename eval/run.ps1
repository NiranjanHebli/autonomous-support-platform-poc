$ErrorActionPreference = "Stop"

Write-Host "Checking if models are trained..."
if (!(Test-Path "Scripts/vectorizer.pkl") -or !(Test-Path "Scripts/model_intent.pkl")) {
    Write-Host "Models not found in Scripts/. Training models first..."
    uv run python Scripts/train.py
}

if (!(Test-Path "eval/test_dataset.csv")) {
    Write-Host "Generating test cases..."
    uv run python eval/generate_test_cases.py
} else {
    Write-Host "Test dataset found. Skipping generation."
}

Write-Host "Evaluating models..."
uv run python eval/evaluate_models.py

Write-Host "Evaluation completed successfully."
