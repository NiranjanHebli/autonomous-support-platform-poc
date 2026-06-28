import sys
import os
import pandas as pd
import numpy as np
import onnxruntime as rt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from eval.add_noise import inject_noise
from core.llm_core import get_ragas_embeddings

def main():
    print("Loading ONNX model...")
    # Adjust this path if the model is located elsewhere
    model_path = "saved_models/m-8a7257ac0857427e9daa6ba9105c4f56/artifacts/model.onnx"
    sess = rt.InferenceSession(model_path)
    input_name = sess.get_inputs()[0].name
    
    print("Loading Embeddings...")
    embeddings_model = get_ragas_embeddings()

    print("Loading test dataset...")
    df = pd.read_csv("eval/test_dataset.csv")
    text_col = 'instruction' if 'instruction' in df.columns else 'utterance'
    
    print("Applying noise to dataset...")
    df['noisy_text'] = df[text_col].apply(inject_noise)
    
    print("Extracting features using embeddings...")
    # Use HuggingFace embeddings
    embeddings = embeddings_model.embed_documents(df['noisy_text'].tolist())
    X_dense = np.asarray(embeddings, dtype=np.float32)
        
    print(f"Running ONNX inference on {len(df)} samples...")
    # The ONNX model returns [label, probabilities]
    preds, probs = sess.run(None, {input_name: X_dense})
    
    df['onnx_prediction'] = preds
    # Add top probability class confidence
    confidences = [p.get(pred, 0.0) if isinstance(p, dict) else p for p, pred in zip(probs, preds)]
    df['onnx_confidence'] = confidences
    
    output_path = "eval/onnx_noisy_results.csv"
    df.to_csv(output_path, index=False)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
