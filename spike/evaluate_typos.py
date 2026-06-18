import sys
import os
import pandas as pd
from textblob import TextBlob

# Add parent directory and scripts directory to path to import score
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "scripts"))
import scripts.score as score


def modify_with_typos(text):
    # simple dictionary of typo injections or simple replacements
    replacements = {
        "password": "pssword",
        "account": "acount",
        "cancel": "cencel",
        "order": "ordr",
        "refund": "refnd",
        "return": "retrn",
        "shipping": "shiping",
        "address": "adres",
        "payment": "paymnt",
        "credit": "credt",
        "card": "crad",
        "customer": "custmer",
        "service": "srvice",
        "support": "suport",
        "help": "hlp",
        "login": "loging",
        "change": "chaneg",
        "update": "updat",
        "delete": "delet",
        "delivery": "delivry",
        "track": "trak",
        "package": "pakage",
        "receive": "recieve",
        "missing": "mising",
        "damaged": "damged",
        "broken": "brokn",
        "wrong": "rong",
        "item": "itm",
        "issue": "isue",
        "problem": "probem",
    }

    words = text.split()
    new_words = []
    for word in words:
        clean_word = word.lower().strip(".,!?")
        if clean_word in replacements:
            new_words.append(replacements[clean_word])
        else:
            new_words.append(word)
    return " ".join(new_words)


queries = [
    "I need help resetting my password.",
    "How do I cancel my order?",
    "Where is my refund?",
    "I want to return an item.",
    "Can you update my shipping address?",
    "My payment was declined.",
    "How do I change my credit card?",
    "I need to speak to customer service.",
    "Can support help me with my login?",
    "I want to delete my account.",
    "When will my delivery arrive?",
    "How can I track my package?",
    "I did not receive my missing item.",
    "My package was damaged in transit.",
    "The item I received is broken.",
    "You sent the wrong item.",
    "I have an issue with my order.",
    "There is a problem with my account.",
    "How do I create a new account?",
    "Can I get a refund for my order?",
    "Where do I find my account settings?",
    "I forgot my login password.",
    "Please cancel my subscription.",
    "How much does shipping cost?",
    "What forms of payment do you accept?",
    "My credit card was charged twice.",
    "Is there a phone number for customer support?",
    "I want to track the delivery of my package.",
    "The item is missing from my package.",
    "How do I update my payment method?",
]


def main():
    print("Loading models from parent directory...")
    # Change to parent directory temporarily to load artifacts
    original_cwd = os.getcwd()
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(parent_dir)
    vectorizer, model_intent, le_intent, model_category, le_category = (
        score.load_artifacts()
    )

    results = []
    matches = 0

    for original in queries:
        modified = modify_with_typos(original)
        fixed_modified = str(TextBlob(modified).correct())

        orig_intent, orig_conf, _, _ = score.predict_utterance(
            original, vectorizer, model_intent, le_intent, model_category, le_category
        )

        mod_intent, mod_conf, _, _ = score.predict_utterance(
            fixed_modified,
            vectorizer,
            model_intent,
            le_intent,
            model_category,
            le_category,
        )

        match = "Y" if orig_intent == mod_intent else "N"
        if match == "Y":
            matches += 1

        results.append(
            {
                "Original Message": original,
                "Modified Message (Typo)": modified,
                "Fixed Message": fixed_modified,
                "Original Intent": orig_intent,
                "Predicted Intent": mod_intent,
                "Original Confidence": f"{orig_conf:.4f}",
                "Confidence": f"{mod_conf:.4f}",
                "Match Y/N": match,
            }
        )

    os.chdir(original_cwd)

    # Save CSV
    df = pd.DataFrame(results)
    df.to_csv("typo_evaluation.csv", index=False)
    print("Saved results to typo_evaluation.csv")

    # Generate FINDINGS.md
    match_rate = matches / len(queries) * 100
    findings = f"""# Typo Evaluation Findings

## Overview
Evaluated {len(queries)} common customer support queries by injecting deliberate typos, then applying TextBlob spell correction, to test the robustness of the BM25 vectorization (with lemmatization) and LightGBM model pipeline.

## Results
- **Total Queries**: {len(queries)}
- **Matches (Intent maintained after typos + spell check)**: {matches}
- **Degradation Rate**: {100 - match_rate:.1f}%

## Conclusion
"""
    if match_rate < 80:
        findings += "Even with TextBlob spell correction, the model degrades significantly on typos. We might need a better spell checker or subword tokenization.\n"
    else:
        findings += "With TextBlob spell correction, the model is reasonably robust to typos. The degradation rate is low, confirming spell checking is an effective preprocessing step.\n"

    with open("FINDINGS.md", "a") as f:
        f.write("\n---\n\n" + findings)

    print("Saved FINDINGS.md")


if __name__ == "__main__":
    main()
