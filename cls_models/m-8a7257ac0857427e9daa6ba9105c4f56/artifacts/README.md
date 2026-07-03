---
language:
- en
- hi
- mr
- bn
- ta
- te
tags:
- text-classification
- onnx
- intent-classification
- customer-support
- multilingual
datasets:
- bitext-cs-train
---

# Agent Intent Classification Model

This model is an ONNX-based classifier designed to route customer support queries to the appropriate agent. It was trained on the `bitext-cs-train.csv` dataset and supports both English and multiple Indian languages.

## Preprocessing

To use this model, the input text must first be converted into dense vector embeddings using the `ibm-granite/granite-embedding-97m-multilingual-r2` model from Hugging Face.

```python
from langchain_huggingface import HuggingFaceEmbeddings
import numpy as np

# 1. Load the embedding model
embeddings_model = HuggingFaceEmbeddings(model_name="ibm-granite/granite-embedding-97m-multilingual-r2")

# 2. Embed the text
text = "I need help with my order."
embedding = embeddings_model.embed_query(text)

# 3. Convert to float32 numpy array
X_dense = np.asarray([embedding], dtype=np.float32)
```

## Inference

Once the input is preprocessed into an embedding vector, it can be passed to the ONNX model for inference.

```python
import onnxruntime as rt

# 1. Load the ONNX model
sess = rt.InferenceSession("model.onnx")
input_name = sess.get_inputs()[0].name

# 2. Run inference
preds, probs = sess.run(None, {input_name: X_dense})

# 3. Map prediction to string class
classes = ['billing', 'order', 'product', 'shipping', 'undefined']
predicted_class = classes[preds[0]]

print(f"Predicted Agent: {predicted_class}")
```

## Classes

The model predicts one of the following 5 classes:
- `billing`
- `order`
- `product`
- `shipping`
- `undefined`


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

