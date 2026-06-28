# ONNX Model Evaluation Report (Noisy Dataset)

This report evaluates the performance and robustness of the ONNX model on the noisy dataset using 5 key metrics. Since ground-truth labels for these specific ONNX classes are not mapped, these metrics focus on the model's confidence, decisiveness, and prediction distribution.

## 1. Average Prediction Confidence
**Score: 0.5474**
- **Definition**: The mean probability score of the model's chosen class across all samples.
- **Interpretation**: A higher score indicates the model is generally very confident in its predictions despite the noise.

## 2. Low Confidence Rate (< 0.6)
**Score: 66.33%**
- **Definition**: The percentage of test samples where the model's confidence fell below 60%.
- **Interpretation**: Indicates the model's susceptibility to the injected noise. A lower percentage is better.

## 3. High Confidence Rate (> 0.8)
**Score: 9.00%**
- **Definition**: The percentage of test samples where the model was highly confident (> 80%).
- **Interpretation**: Shows how much of the noisy dataset the model still considers "easy" to predict.

## 4. Class Distribution Entropy
**Score: 1.2244**
- **Definition**: The Shannon entropy of the predicted class distribution.
- **Interpretation**: Evaluates prediction bias. A very low entropy suggests the model collapses to predicting only 1 or 2 classes when faced with noise, while higher entropy indicates it still utilizes its full output space.

## 5. Model Decisiveness (Confidence Variance)
**Score: 0.0233**
- **Definition**: The statistical variance of the confidence scores.
- **Interpretation**: A healthy variance means the model distinguishes between clear signals and noisy inputs, rather than predicting everything with a flat, uniform confidence.

### Prediction Distribution Breakdown
| Predicted Class | Count | Percentage |
|---|---|---|
| 4 | 129 | 43.00% |
| 1 | 112 | 37.33% |
| 0 | 35 | 11.67% |
| 3 | 19 | 6.33% |
| 2 | 5 | 1.67% |
