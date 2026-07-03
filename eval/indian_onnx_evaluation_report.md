# ONNX Model Multilingual Evaluation Report (Target: Agent)

This report evaluates the ONNX model's ability to predict the `agent` column across different Indian languages and English. Embeddings used: `ibm-granite/granite-embedding-97m-multilingual-r2`.

## Overall Metrics

- **Accuracy**: 0.6914
- **Precision (Weighted)**: 0.7091
- **Recall (Weighted)**: 0.6914
- **F1 Score (Weighted)**: 0.6874

## Metrics by Language

| Language | Samples | Accuracy | Precision | Recall | F1 Score |
|---|---|---|---|---|---|
| en | 54 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| hi | 54 | 0.9074 | 0.9235 | 0.9074 | 0.9055 |
| bn | 54 | 0.7593 | 0.7661 | 0.7593 | 0.7497 |
| te | 54 | 0.5741 | 0.5756 | 0.5741 | 0.4982 |
| ta | 54 | 0.2407 | 0.2923 | 0.2407 | 0.2372 |
| mr | 54 | 0.6667 | 0.6665 | 0.6667 | 0.6623 |

## Production Eligibility Analysis

For the model to be eligible for production in Indian languages, we expect the F1 score in the translated languages to be comparable to English. If scores are significantly lower, the ONNX model (which was likely trained on English embeddings) might not generalize well even with multilingual embeddings, or it needs fine-tuning on the multilingual embedding space.

