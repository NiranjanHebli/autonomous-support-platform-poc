from datasets import load_dataset
import pandas as pd
import os
import shutil

print("Loading dataset...")
ds = load_dataset(
    "bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train"
)
df = ds.to_pandas()

print("Columns:", df.columns.tolist())

if "intent" in df.columns and "response" in df.columns:
    unique_intents = df.groupby("intent").first().reset_index()
    print(f"Found {len(unique_intents)} unique intents.")

    if os.path.exists("data/policies"):
        shutil.rmtree("data/policies")
    os.makedirs("data/policies", exist_ok=True)

    count = 0
    for i, row in unique_intents.head(30).iterrows():
        intent_name = row["intent"].replace("_", " ").title()
        filename = row["intent"].replace(" ", "_").lower() + ".md"
        content = f"# {intent_name}\n\n{row['response']}\n"
        with open(os.path.join("data/policies", filename), "w") as f:
            f.write(content)
        count += 1

    print(f"Generated {count} policy documents in data/policies/")
else:
    print("Missing expected columns. Found:", df.columns.tolist())
