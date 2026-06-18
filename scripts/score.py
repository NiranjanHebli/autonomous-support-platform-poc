import pickle
import sys
import os
import warnings
from Scripts.text_preprocessing import preprocess_text, BM25Transformer

warnings.filterwarnings("ignore", category=UserWarning, message="X does not have valid feature names")

def load_artifacts():
    base_dir = os.path.dirname(__file__)
    try:
        with open(os.path.join(base_dir, "vectorizer.pkl"), "rb") as f:
            vectorizer = pickle.load(f)
            
        with open(os.path.join(base_dir, "model_intent.pkl"), "rb") as f:
            model_intent = pickle.load(f)
        with open(os.path.join(base_dir, "label_encoder_intent.pkl"), "rb") as f:
            le_intent = pickle.load(f)
            
        with open(os.path.join(base_dir, "model_category.pkl"), "rb") as f:
            model_category = pickle.load(f)
        with open(os.path.join(base_dir, "label_encoder_category.pkl"), "rb") as f:
            le_category = pickle.load(f)

        return vectorizer, model_intent, le_intent, model_category, le_category
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure you have run 'train.py' first to generate all models.")
        sys.exit(1)


def predict_target(X, model, label_encoder, threshold=0.60):
    pred_idx = model.predict(X)[0]
    probs = model.predict_proba(X)[0]
    confidence = probs[pred_idx]

    if confidence < threshold:
        return "UNDEFINED", confidence

    label = label_encoder.inverse_transform([pred_idx])[0]
    return label, confidence


def predict_utterance(
    text, vectorizer, model_intent, le_intent, model_category, le_category
):
    X = vectorizer.transform([text])

    intent, intent_conf = predict_target(X, model_intent, le_intent)
    category, cat_conf = predict_target(X, model_category, le_category)

    return intent, intent_conf, category, cat_conf


def main():
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "I need help resetting my password."
        print(f"No text provided. Using default text: '{text}'")

    print("Loading model artifacts...")
    vectorizer, model_intent, le_intent, model_category, le_category = load_artifacts()

    print("Running inference...\n")
    intent, intent_conf, category, cat_conf = predict_utterance(
        text, vectorizer, model_intent, le_intent, model_category, le_category
    )

    print(f"Text: '{text}'")
    print(f"Predicted Intent:   {intent} (Confidence: {intent_conf:.4f})")
    print(f"Predicted Category: {category} (Confidence: {cat_conf:.4f})")


if __name__ == "__main__":
    main()
