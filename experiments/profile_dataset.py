import pandas as pd
from datasets import load_dataset
import os

def main():
    print("Loading dataset from Hugging Face...")
    dataset = load_dataset(
        "bitext/Bitext-customer-support-llm-chatbot-training-dataset"
    )
    
    print("Loading data into pandas DataFrame...")
    df = dataset["train"].to_pandas()
    
    print("\n" + "="*50)
    print("Ticket Distribution (Category)")
    print("="*50)
    if 'category' in df.columns:
        print(df['category'].value_counts(dropna=False))
    else:
        print("Column 'category' not found.")
        
    print("\n" + "="*50)
    print("Intent Analysis (Intent)")
    print("="*50)
    if 'intent' in df.columns:
        print(df['intent'].value_counts(dropna=False))
    else:
        print("Column 'intent' not found.")
        
    print("\n" + "="*50)
    print("Dataset Info")
    print("="*50)
    df.info()

if __name__ == "__main__":
    main()
