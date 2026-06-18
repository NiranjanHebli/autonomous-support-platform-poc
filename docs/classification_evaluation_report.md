# Model Evaluation Report

## Overview
This report documents the performance metrics of the customer support text classification models (`model_intent.pkl` and `model_category.pkl`). The evaluation was conducted on a stratified test dataset of 300 samples with noise injection (typos and missing characters) to simulate real-world noisy user inputs.

## Evaluation Results

### Intent Classification Metrics
The model's performance on predicting the specific intent of the user's query:

* **Accuracy:** 0.9000
* **Macro Precision:** 0.9230
* **Macro Recall:** 0.8674
* **Macro F1-Score:** 0.8871
* **MCC (Matthew's Correlation Coefficient):** 0.8979

### Category Classification Metrics
The model's performance on predicting the high-level category of the user's query:

* **Accuracy:** 0.9400
* **Macro Precision:** 0.8745
* **Macro Recall:** 0.8574
* **Macro F1-Score:** 0.8623
* **MCC (Matthew's Correlation Coefficient):** 0.9329

## Execution Details
The evaluation was executed using the automated testing suite:
```powershell
PS C:\Developer\Codebase\autonomous-support-platform-poc> ./eval/run.ps1
Checking if models are trained...
Test dataset found. Skipping generation.
Evaluating models...
Loading test cases...
Loading model artifacts...
Running inference on 300 test cases...
```
