Pipeline: Social Media Message Ingest → Text Cleaning (strip whitespace/newlines) → TF-IDF Vectorization (10k features, english stop words) → LightGBM Classifiers (Category & Intent) → Confidence Threshold Filter (< 0.60 defaults to 'UNDEFINED') → Structured JSON Output.

Data Contracts: Input Payload (from Social Media Client):

json
{
  "room_id": "!xyz:Social Media.org",
  "event_id": "$abc123def",
  "sender": "@customer:Social Media.org",
  "text": "I need help claiming refund for my returned order."
}
Classification Output (score.py):

json
{
  "event_id": "$abc123def",
  "predicted_intent": "refund_request",
  "intent_confidence": 0.8921,
  "predicted_category": "REFUND",
  "category_confidence": 0.9104
}
Model Choice Justification: LightGBM paired with TF-IDF was selected over deep learning embeddings (e.g., Transformers) to eliminate the need for GPU hardware, vastly reduce local inference latency (<50ms), and ensure the score.py script remains lightweight and easy to deploy alongside the Social Media CLI.

Bounded Downstream Action: The Social Media bot will automatically append a colored tag (e.g., "[ACCOUNT_MANAGEMENT]") or forward the message event to the corresponding department-specific Social Media room if confidence > 0.60.