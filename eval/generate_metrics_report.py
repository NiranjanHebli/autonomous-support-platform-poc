import pandas as pd
import numpy as np
import os
from collections import Counter
from scipy.stats import entropy

def generate_report():
    results_file = "eval/onnx_noisy_results.csv"
    if not os.path.exists(results_file):
        print(f"Results file {results_file} not found. Please run test_onnx.py first.")
        return
        
    df = pd.read_csv(results_file)
    
    if 'onnx_confidence' not in df.columns or 'onnx_prediction' not in df.columns:
        print("Missing required columns in results file.")
        return
        
    confidences = df['onnx_confidence'].values
    predictions = df['onnx_prediction'].values
    
    # Metric 1: Average Prediction Confidence
    avg_confidence = np.mean(confidences)
    
    # Metric 2: Low Confidence Rate (< 0.6)
    low_conf_rate = np.mean(confidences < 0.6) * 100
    
    # Metric 3: High Confidence Rate (> 0.8)
    high_conf_rate = np.mean(confidences > 0.8) * 100
    
    # Metric 4: Class Distribution Entropy
    # Measures how evenly distributed the predictions are across the classes
    class_counts = list(Counter(predictions).values())
    class_probs = np.array(class_counts) / sum(class_counts)
    pred_entropy = entropy(class_probs)
    
    # Metric 5: Model Decisiveness (Confidence Variance)
    # How varied the confidences are across the dataset. High variance means 
    # the model can clearly distinguish between easy and hard samples.
    conf_variance = np.var(confidences)
    
    # Generate Markdown content
    md_content = f"""# ONNX Model Evaluation Report (Noisy Dataset)

This report evaluates the performance and robustness of the ONNX model on the noisy dataset using 5 key metrics. Since ground-truth labels for these specific ONNX classes are not mapped, these metrics focus on the model's confidence, decisiveness, and prediction distribution.

## 1. Average Prediction Confidence
**Score: {avg_confidence:.4f}**
- **Definition**: The mean probability score of the model's chosen class across all samples.
- **Interpretation**: A higher score indicates the model is generally very confident in its predictions despite the noise.

## 2. Low Confidence Rate (< 0.6)
**Score: {low_conf_rate:.2f}%**
- **Definition**: The percentage of test samples where the model's confidence fell below 60%.
- **Interpretation**: Indicates the model's susceptibility to the injected noise. A lower percentage is better.

## 3. High Confidence Rate (> 0.8)
**Score: {high_conf_rate:.2f}%**
- **Definition**: The percentage of test samples where the model was highly confident (> 80%).
- **Interpretation**: Shows how much of the noisy dataset the model still considers "easy" to predict.

## 4. Class Distribution Entropy
**Score: {pred_entropy:.4f}**
- **Definition**: The Shannon entropy of the predicted class distribution.
- **Interpretation**: Evaluates prediction bias. A very low entropy suggests the model collapses to predicting only 1 or 2 classes when faced with noise, while higher entropy indicates it still utilizes its full output space.

## 5. Model Decisiveness (Confidence Variance)
**Score: {conf_variance:.4f}**
- **Definition**: The statistical variance of the confidence scores.
- **Interpretation**: A healthy variance means the model distinguishes between clear signals and noisy inputs, rather than predicting everything with a flat, uniform confidence.

### Prediction Distribution Breakdown
"""
    
    # Add class distribution table
    md_content += "| Predicted Class | Count | Percentage |\n"
    md_content += "|---|---|---|\n"
    
    total = len(predictions)
    for cls, count in Counter(predictions).most_common():
        pct = (count / total) * 100
        md_content += f"| {cls} | {count} | {pct:.2f}% |\n"
        
    # Write to Markdown file
    output_md = "eval/onnx_evaluation_report.md"
    with open(output_md, "w") as f:
        f.write(md_content)
        
    print(f"Evaluation report successfully generated and saved to {output_md}")

if __name__ == "__main__":
    generate_report()
