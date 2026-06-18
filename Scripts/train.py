import pandas as pd
import lightgbm as lgb
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from text_preprocessing import preprocess_text, BM25Transformer
import pickle
import os
from datasets import load_dataset
from dotenv import load_dotenv

def main():
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")
    
    print("Downloading dataset from Hugging Face...")
    dataset = load_dataset(
        "bitext/Bitext-customer-support-llm-chatbot-training-dataset",
        token=hf_token
    )
    
    print("Loading data into pandas DataFrame...")
    df = dataset['train'].to_pandas()
    
    print(f"Columns in dataset: {df.columns.tolist()}")
    
    print("Handling unclear or multiple values for category and intent...")
    for col in ['category', 'intent']:
        if col in df.columns:
            # Convert to string to check for multiple values and handle missing
            df[col] = df[col].astype(str).fillna('')
            # Default to 'UNDEFINED' if empty, contains separators (like comma or pipe), or is literally 'nan'
            df[col] = df[col].apply(
                lambda x: 'UNDEFINED' if not x.strip() or x.strip().lower() == 'nan' or ',' in x or '|' in x else x
            )

    print("Downcasting categorical columns...")
    for col in ['category', 'intent', 'flags']:
        if col in df.columns:
            df[col] = df[col].astype('category')
            print(f"Downcasted {col} to categorical.")
    
    # Determine text column
    text_col = 'instruction' if 'instruction' in df.columns else 'utterance'
    if 'utterance' in df.columns: text_col = 'utterance'
    
    print(f"Using text column: '{text_col}'")
    
    # Drop rows where text is missing
    df = df.dropna(subset=[text_col])
    
    print("BM25 Vectorization with Custom Preprocessing...")
    vectorizer = Pipeline([
        ('count', CountVectorizer(analyzer=preprocess_text, max_features=10000)),
        ('bm25', BM25Transformer())
    ])
    X = vectorizer.fit_transform(df[text_col])
    
    with open("vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
        
    targets = ['intent', 'category']
    for target in targets:
        print(f"\n--- Training model for {target} ---")
        if target not in df.columns:
            print(f"Warning: {target} not found in columns. Skipping.")
            continue
            
        # Label encoding
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(df[target])
        
        # Save label encoder
        with open(f"label_encoder_{target}.pkl", "wb") as f:
            pickle.dump(label_encoder, f)
            
        print("Splitting data...")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print(f"Training LightGBM model for {target}...")
        model = lgb.LGBMClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        print(f"Evaluating {target} model...")
        score = model.score(X_test, y_test)
        print(f"Accuracy on test set for {target}: {score:.4f}")
        
        print(f"Saving {target} model artifact...")
        with open(f"model_{target}.pkl", "wb") as f:
            pickle.dump(model, f)
            
    print("\nDone! All artifacts saved.")

if __name__ == "__main__":
    main()
