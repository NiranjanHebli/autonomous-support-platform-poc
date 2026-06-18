import pandas as pd
import random

replacements = {
    "password": "pssword", "account": "acount", "cancel": "cencel", "order": "ordr",
    "refund": "refnd", "return": "retrn", "shipping": "shiping", "address": "adres",
    "payment": "paymnt", "credit": "credt", "card": "crad", "customer": "custmer",
    "service": "srvice", "support": "suport", "help": "hlp", "login": "loging",
    "change": "chaneg", "update": "updat", "delete": "delet", "delivery": "delivry",
    "track": "trak", "package": "pakage", "receive": "recieve", "missing": "mising",
    "damaged": "damged", "broken": "brokn", "wrong": "rong", "item": "itm",
    "issue": "isue", "problem": "probem"
}

def inject_noise(text):
    if not isinstance(text, str): return text
    words = text.split()
    new_words = []
    for word in words:
        clean_word = word.lower().strip(".,!?")
        if clean_word in replacements and random.random() < 0.7:
            new_words.append(replacements[clean_word])
        else:
            if len(word) > 4 and random.random() < 0.2:
                idx = random.randint(1, len(word)-2)
                new_words.append(word[:idx] + word[idx+1:])
            else:
                new_words.append(word)
    return " ".join(new_words)

def main():
    df = pd.read_csv('eval/test_dataset.csv')
    text_col = 'instruction' if 'instruction' in df.columns else 'utterance'
    if 'utterance' in df.columns: text_col = 'utterance'
    
    random.seed(42)
    # Apply to 60% of dataset
    indices = df.sample(frac=0.6, random_state=42).index
    df.loc[indices, text_col] = df.loc[indices, text_col].apply(inject_noise)
    
    df.to_csv('eval/test_dataset.csv', index=False)
    print("Noise injected into eval/test_dataset.csv")

if __name__ == '__main__':
    main()
