import os
import pandas as pd
from datasets import load_dataset
from dotenv import load_dotenv

def clean_column(df, col):
    if col in df.columns:
        df[col] = df[col].astype(str).fillna('')
        df[col] = df[col].apply(
            lambda x: 'UNDEFINED' if not x.strip() or x.strip().lower() == 'nan' or ',' in x or '|' in x else x
        )
    return df

def generate_test_cases():
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")
    
    print("Downloading dataset from Hugging Face...")
    dataset = load_dataset(
        "bitext/Bitext-customer-support-llm-chatbot-training-dataset",
        token=hf_token
    )
    
    print("Loading data into pandas DataFrame...")
    df = dataset['train'].to_pandas()
    
    print("Handling unclear or multiple values for category and intent...")
    df = clean_column(df, 'category')
    df = clean_column(df, 'intent')
    
    text_col = 'instruction' if 'instruction' in df.columns else 'utterance'
    if 'utterance' in df.columns: text_col = 'utterance'
    
    df = df.dropna(subset=[text_col])
    
    df['stratify_group'] = df['category'] + "|||" + df['intent']
    
    target_samples = 300
    unique_groups = df['stratify_group'].nunique()
    print(f"Total unique category/intent combinations: {unique_groups}")
    
    samples_per_group = max(1, target_samples // unique_groups)
    
    sampled_dfs = []
    total_sampled = 0
    for name, group in df.groupby('stratify_group'):
        n_samples = min(samples_per_group, len(group))
        sampled_dfs.append(group.sample(n_samples, random_state=42))
        total_sampled += n_samples
        
    sampled_df = pd.concat(sampled_dfs)
    
    if len(sampled_df) < target_samples:
        remaining = target_samples - len(sampled_df)
        remaining_df = df.drop(sampled_df.index)
        if len(remaining_df) >= remaining:
            additional_samples = remaining_df.sample(remaining, random_state=42)
            sampled_df = pd.concat([sampled_df, additional_samples])
        else:
            sampled_df = pd.concat([sampled_df, remaining_df])
            
    if len(sampled_df) > target_samples:
        sampled_df = sampled_df.sample(target_samples, random_state=42)
        
    print(f"Generated {len(sampled_df)} test cases.")
    
    os.makedirs('eval', exist_ok=True)
    sampled_df.to_csv('eval/test_dataset.csv', index=False)
    print("Saved test cases to eval/test_dataset.csv")

if __name__ == "__main__":
    generate_test_cases()
