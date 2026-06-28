import os
import sys
import pandas as pd
import numpy as np
import onnxruntime as rt
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from langchain_huggingface import HuggingFaceEmbeddings
import warnings

warnings.filterwarnings('ignore')

def main():
    dataset_path = "eval/indian_multilingual_dataset.csv"
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return

    print("Loading ONNX model...")
    model_path = "saved_models/m-8a7257ac0857427e9daa6ba9105c4f56/artifacts/model.onnx"
    if not os.path.exists(model_path):
        print(f"ONNX model not found at {model_path}")
        return
        
    sess = rt.InferenceSession(model_path)
    input_name = sess.get_inputs()[0].name
    
    print("Loading ibm-granite/granite-embedding-97m-multilingual-r2 Embeddings...")
    embeddings_model = HuggingFaceEmbeddings(model_name="ibm-granite/granite-embedding-97m-multilingual-r2")

    print("Loading test dataset...")
    df = pd.read_csv(dataset_path)
    
    if 'language' not in df.columns or 'instruction' not in df.columns or 'agent' not in df.columns:
        print("Missing required columns ('language', 'instruction', 'agent') in dataset.")
        return

    print("Extracting features using embeddings...")
    embeddings = embeddings_model.embed_documents(df['instruction'].tolist())
    X_dense = np.asarray(embeddings, dtype=np.float32)
        
    print(f"Running ONNX inference on {len(df)} samples...")
    preds, probs = sess.run(None, {input_name: X_dense})
    
    # Map ONNX int predictions to agent strings
    classes = ['billing', 'order', 'product', 'shipping', 'undefined']
    df['onnx_prediction_int'] = preds
    df['onnx_prediction'] = [classes[p] for p in preds]
    confidences = [p.get(pred, 0.0) if isinstance(p, dict) else p for p, pred in zip(probs, preds)]
    df['onnx_confidence'] = confidences
    
    # Save the results
    results_path = "eval/indian_onnx_results.csv"
    df.to_csv(results_path, index=False)
    print(f"Inference results saved to {results_path}")

    print("Generating evaluation report...")
    generate_report(df)

def generate_report(df):
    languages = df['language'].unique()
    
    md_content = "# ONNX Model Multilingual Evaluation Report (Target: Agent)\n\n"
    md_content += "This report evaluates the ONNX model's ability to predict the `agent` column across different Indian languages and English. "
    md_content += "Embeddings used: `ibm-granite/granite-embedding-97m-multilingual-r2`.\n\n"
    
    md_content += "## Overall Metrics\n\n"
    
    y_true = df['agent']
    y_pred = df['onnx_prediction']
    
    overall_acc = accuracy_score(y_true, y_pred)
    overall_prec = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    overall_rec = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    overall_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    md_content += f"- **Accuracy**: {overall_acc:.4f}\n"
    md_content += f"- **Precision (Weighted)**: {overall_prec:.4f}\n"
    md_content += f"- **Recall (Weighted)**: {overall_rec:.4f}\n"
    md_content += f"- **F1 Score (Weighted)**: {overall_f1:.4f}\n\n"
    
    md_content += "## Metrics by Language\n\n"
    
    md_content += "| Language | Samples | Accuracy | Precision | Recall | F1 Score |\n"
    md_content += "|---|---|---|---|---|---|\n"
    
    for lang in languages:
        lang_df = df[df['language'] == lang]
        if len(lang_df) == 0:
            continue
            
        l_y_true = lang_df['agent']
        l_y_pred = lang_df['onnx_prediction']
        
        acc = accuracy_score(l_y_true, l_y_pred)
        prec = precision_score(l_y_true, l_y_pred, average='weighted', zero_division=0)
        rec = recall_score(l_y_true, l_y_pred, average='weighted', zero_division=0)
        f1 = f1_score(l_y_true, l_y_pred, average='weighted', zero_division=0)
        
        md_content += f"| {lang} | {len(lang_df)} | {acc:.4f} | {prec:.4f} | {rec:.4f} | {f1:.4f} |\n"
    
    md_content += "\n## Production Eligibility Analysis\n\n"
    md_content += "For the model to be eligible for production in Indian languages, we expect the F1 score in the translated languages to be comparable to English. "
    md_content += "If scores are significantly lower, the ONNX model (which was likely trained on English embeddings) might not generalize well even with multilingual embeddings, or it needs fine-tuning on the multilingual embedding space.\n\n"
    
    output_md = "eval/indian_onnx_evaluation_report.md"
    with open(output_md, "w") as f:
        f.write(md_content)
        
    print(f"Evaluation report successfully generated and saved to {output_md}")

if __name__ == "__main__":
    main()
