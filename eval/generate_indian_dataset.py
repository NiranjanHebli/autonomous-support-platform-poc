import os
import pandas as pd
from deep_translator import GoogleTranslator
from tqdm import tqdm
import time

def generate_indian_dataset():
    input_file = '../bitext-cs-train.csv'
    if not os.path.exists(input_file):
        input_file = 'bitext-cs-train.csv' # Handle running from root
        
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    # Sample to keep translation time reasonable.
    # Group by intent to get a diverse set of examples.
    print("Sampling data...")
    sampled_dfs = []
    
    # Sample max 2 from each intent, up to ~100 samples
    for name, group in df.groupby('intent'):
        sampled_dfs.append(group.sample(min(2, len(group)), random_state=42))
        
    sampled_df = pd.concat(sampled_dfs).sample(frac=1, random_state=42).head(100)
    print(f"Sampled {len(sampled_df)} rows for translation.")
    
    indian_langs = {
        'hi': 'Hindi',
        'bn': 'Bengali',
        'te': 'Telugu',
        'ta': 'Tamil',
        'mr': 'Marathi'
    }
    
    translated_data = []
    
    for idx, row in tqdm(sampled_df.iterrows(), total=len(sampled_df)):
        original_text = str(row['instruction'])
        category = row['category']
        intent = row['intent']
        agent = row['agent'] if 'agent' in row else ''
        
        # Keep original English
        translated_data.append({
            'instruction': original_text,
            'category': category,
            'intent': intent,
            'agent': agent,
            'language': 'en'
        })
        
        # Translate to Indian languages
        for lang_code, lang_name in indian_langs.items():
            try:
                translated_text = GoogleTranslator(source='auto', target=lang_code).translate(original_text)
                translated_data.append({
                    'instruction': translated_text,
                    'category': category,
                    'intent': intent,
                    'agent': agent,
                    'language': lang_code
                })
            except Exception as e:
                print(f"Error translating to {lang_name}: {e}")
                
            time.sleep(0.1) # Be nice to the API
            
    output_df = pd.DataFrame(translated_data)
    output_path = 'indian_multilingual_dataset.csv' if os.path.basename(os.getcwd()) == 'eval' else 'eval/indian_multilingual_dataset.csv'
    
    output_df.to_csv(output_path, index=False)
    print(f"Generated multilingual dataset with {len(output_df)} samples at {output_path}")

if __name__ == "__main__":
    generate_indian_dataset()
