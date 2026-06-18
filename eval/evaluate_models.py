import sys
import os
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, matthews_corrcoef

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Scripts')))

import Scripts.score as score

def compute_metrics(y_true, y_pred, target_name):
    acc = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    mcc = matthews_corrcoef(y_true, y_pred)
    
    print(f"--- {target_name.upper()} METRICS ---")
    print(f"Accuracy:        {acc:.4f}")
    print(f"Macro Precision: {precision:.4f}")
    print(f"Macro Recall:    {recall:.4f}")
    print(f"Macro F1-Score:  {f1:.4f}")
    print(f"MCC:             {mcc:.4f}\n")

def evaluate_models():
    root_dir = os.path.join(os.path.dirname(__file__), '..')
    os.chdir(root_dir)
    
    print("Loading test cases...")
    try:
        df = pd.read_csv('eval/test_dataset.csv')
    except FileNotFoundError:
        print("Test dataset not found. Please run eval/generate_test_cases.py first.")
        sys.exit(1)
    
    text_col = 'instruction' if 'instruction' in df.columns else 'utterance'
    if 'utterance' in df.columns: text_col = 'utterance'
    
    print("Loading model artifacts...")
    vectorizer, model_intent, le_intent, model_category, le_category = score.load_artifacts()
    
    print(f"Running inference on {len(df)} test cases...")
    
    pred_intents = []
    pred_categories = []
    
    for _, row in df.iterrows():
        text = str(row[text_col])
        intent, _, category, _ = score.predict_utterance(
            text, vectorizer, model_intent, le_intent, model_category, le_category
        )
        pred_intents.append(intent)
        pred_categories.append(category)
        
    print("\nComputing metrics...")
    compute_metrics(df['intent'], pred_intents, "Intent")
    compute_metrics(df['category'], pred_categories, "Category")
    
if __name__ == "__main__":
    evaluate_models()
