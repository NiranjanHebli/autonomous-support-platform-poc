Core deliverables (Tier C, ~1 day)
1. PRD (1–2 pages, in Cloudairy AI Docs)
Problem + Cost: Customer support agents are spending ~30% of their time manually reading and triaging inbound Matrix messages to the correct department (e.g., Billing, Tech Support, Refunds). This manual triage costs approximately $4,500/month in agent hours and delays first-response times by an average of 45 minutes.

Top 3 User Stories:

As a customer, I want my support query to reach the correct department immediately so that my issue is resolved faster.
As a support agent, I want incoming Matrix messages to be pre-categorized so that I only see tickets relevant to my expertise.
As a support manager, I want to see a confidence score for automated routing so I can review low-confidence categorization.
Scope:

In Scope: Categorization of English text messages from Matrix rooms; predicting Category and Intent; filtering out low-confidence (<0.60) predictions; CLI tool for inference.
Out of Scope: Voice/audio message classification; automated ticket resolution (bot replies); multi-lingual support.
Requirements:

Functional: Model must predict Intent and Category from a text string. The pipeline must fallback to 'UNDEFINED' if confidence is below 0.60.
Non-functional: Inference latency under 200ms per message. Model must run locally without cloud GPU dependencies.
KPIs (with definitions, targets, and floors):

Macro F1-Score: Harmonic mean of precision and recall across all intents. Target: >0.85. Floor: 0.75.
Intent Match Rate: Percentage of messages where predicted intent exactly matches human labels. Target: >90%. Floor: 80%.
p95 Latency: Time to run text through TF-IDF and LightGBM inference. Target: <50ms. Floor: <200ms.
Automated Route Rate (Business KPI): Percentage of inbound Matrix messages successfully categorized (Confidence > 0.60) without human intervention. Target: >75%. Floor: 60%.
2. Technical Design Doc (1–2 pages)
Pipeline: Matrix Message Ingest → Text Cleaning (strip whitespace/newlines) → TF-IDF Vectorization (10k features, english stop words) → LightGBM Classifiers (Category & Intent) → Confidence Threshold Filter (< 0.60 defaults to 'UNDEFINED') → Structured JSON Output.

Data Contracts: Input Payload (from Matrix Client):

json
{
  "room_id": "!xyz:matrix.org",
  "event_id": "$abc123def",
  "sender": "@customer:matrix.org",
  "text": "I need help resetting my password."
}
Classification Output (score.py):

json
{
  "event_id": "$abc123def",
  "predicted_intent": "password_reset",
  "intent_confidence": 0.8921,
  "predicted_category": "ACCOUNT_MANAGEMENT",
  "category_confidence": 0.9104
}
Model Choice Justification: LightGBM paired with TF-IDF was selected over deep learning embeddings (e.g., Transformers) to eliminate the need for GPU hardware, vastly reduce local inference latency (<50ms), and ensure the score.py script remains lightweight and easy to deploy alongside the Matrix CLI.

Bounded Downstream Action: The Matrix bot will automatically append a colored tag (e.g., "[ACCOUNT_MANAGEMENT]") or forward the message event to the corresponding department-specific Matrix room if confidence > 0.60.

3. Diagrams (Cloudairy)
Deliverables: Architecture diagram (showing Matrix Client → main.py → score.py → Models) + request sequence diagram (Matrix Event → TF-IDF → Classifier → Routing Decision).
Format: Exported as PNG to /diagrams/system_architecture.png and /diagrams/inference_sequence.png.
4. Risk Register
TF-IDF Semantic Limitations
Likelihood: High | Impact: Medium
Mitigation: Re-train with a fallback sentence-transformer model if TF-IDF fails to catch synonyms/paraphrasing not present in the Bitext training data.
Matrix Rate Limiting
Likelihood: Medium | Impact: High
Mitigation: Implement exponential backoff in the Matrix client's send_message and get_messages functions.
Class Imbalance in Training Data
Likelihood: Medium | Impact: Medium
Mitigation: Use class_weight='balanced' in LightGBM if certain categories consistently underperform.
Out-of-Domain Gibberish Messages
Likelihood: High | Impact: Low
Mitigation: The 0.60 confidence threshold in score.py will catch most of these and safely default to 'UNDEFINED'.
Slow Matrix Room Joins
Likelihood: Low | Impact: Medium
Mitigation: Only call client.join_room when explicitly necessary or cache joined room states locally.
Riskiest Assumption: That TF-IDF vectorization will generalize well to actual user typos and slang. Because TF-IDF relies on exact word matches, user messages with severe typos (e.g., "pssword rset") might not trigger the correct LightGBM decision trees, unlike an embedding model which might capture the semantic closeness.

5. De-risk Spike (~2–3 hrs code)
Python Script: Create a local test script evaluate_typos.py that takes 30 common customer support queries, injects common typos/slang, and runs them through score.py.
Outputs:
A CSV table (Original Message → Modified Message → Predicted Intent → Confidence → Match Y/N).
A FINDINGS.md summarizing if the TF-IDF model degrades completely on typos, determining if we need to implement spell-check preprocessing before vectorization.Core deliverables (Tier C, ~1 day)
1. PRD (1–2 pages, in Cloudairy AI Docs)
Problem + Cost: Customer support agents are spending ~30% of their time manually reading and triaging inbound Matrix messages to the correct department (e.g., Billing, Tech Support, Refunds). This manual triage costs approximately $4,500/month in agent hours and delays first-response times by an average of 45 minutes.

Top 3 User Stories:

As a customer, I want my support query to reach the correct department immediately so that my issue is resolved faster.
As a support agent, I want incoming Matrix messages to be pre-categorized so that I only see tickets relevant to my expertise.
As a support manager, I want to see a confidence score for automated routing so I can review low-confidence categorization.
Scope:

In Scope: Categorization of English text messages from Matrix rooms; predicting Category and Intent; filtering out low-confidence (<0.60) predictions; CLI tool for inference.
Out of Scope: Voice/audio message classification; automated ticket resolution (bot replies); multi-lingual support.
Requirements:

Functional: Model must predict Intent and Category from a text string. The pipeline must fallback to 'UNDEFINED' if confidence is below 0.60.
Non-functional: Inference latency under 200ms per message. Model must run locally without cloud GPU dependencies.
KPIs (with definitions, targets, and floors):

Macro F1-Score: Harmonic mean of precision and recall across all intents. Target: >0.85. Floor: 0.75.
Intent Match Rate: Percentage of messages where predicted intent exactly matches human labels. Target: >90%. Floor: 80%.
p95 Latency: Time to run text through TF-IDF and LightGBM inference. Target: <50ms. Floor: <200ms.
Automated Route Rate (Business KPI): Percentage of inbound Matrix messages successfully categorized (Confidence > 0.60) without human intervention. Target: >75%. Floor: 60%.
2. Technical Design Doc (1–2 pages)
Pipeline: Matrix Message Ingest → Text Cleaning (strip whitespace/newlines) → TF-IDF Vectorization (10k features, english stop words) → LightGBM Classifiers (Category & Intent) → Confidence Threshold Filter (< 0.60 defaults to 'UNDEFINED') → Structured JSON Output.

Data Contracts: Input Payload (from Matrix Client):

json
{
  "room_id": "!xyz:matrix.org",
  "event_id": "$abc123def",
  "sender": "@customer:matrix.org",
  "text": "I need help resetting my password."
}
Classification Output (score.py):

json
{
  "event_id": "$abc123def",
  "predicted_intent": "password_reset",
  "intent_confidence": 0.8921,
  "predicted_category": "ACCOUNT_MANAGEMENT",
  "category_confidence": 0.9104
}
Model Choice Justification: LightGBM paired with TF-IDF was selected over deep learning embeddings (e.g., Transformers) to eliminate the need for GPU hardware, vastly reduce local inference latency (<50ms), and ensure the score.py script remains lightweight and easy to deploy alongside the Matrix CLI.

Bounded Downstream Action: The Matrix bot will automatically append a colored tag (e.g., "[ACCOUNT_MANAGEMENT]") or forward the message event to the corresponding department-specific Matrix room if confidence > 0.60.

3. Diagrams (Cloudairy)
Deliverables: Architecture diagram (showing Matrix Client → main.py → score.py → Models) + request sequence diagram (Matrix Event → TF-IDF → Classifier → Routing Decision).
Format: Exported as PNG to /diagrams/system_architecture.png and /diagrams/inference_sequence.png.
4. Risk Register
TF-IDF Semantic Limitations
Likelihood: High | Impact: Medium
Mitigation: Re-train with a fallback sentence-transformer model if TF-IDF fails to catch synonyms/paraphrasing not present in the Bitext training data.
Matrix Rate Limiting
Likelihood: Medium | Impact: High
Mitigation: Implement exponential backoff in the Matrix client's send_message and get_messages functions.
Class Imbalance in Training Data
Likelihood: Medium | Impact: Medium
Mitigation: Use class_weight='balanced' in LightGBM if certain categories consistently underperform.
Out-of-Domain Gibberish Messages
Likelihood: High | Impact: Low
Mitigation: The 0.60 confidence threshold in score.py will catch most of these and safely default to 'UNDEFINED'.
Slow Matrix Room Joins
Likelihood: Low | Impact: Medium
Mitigation: Only call client.join_room when explicitly necessary or cache joined room states locally.
Riskiest Assumption: That TF-IDF vectorization will generalize well to actual user typos and slang. Because TF-IDF relies on exact word matches, user messages with severe typos (e.g., "pssword rset") might not trigger the correct LightGBM decision trees, unlike an embedding model which might capture the semantic closeness.

5. De-risk Spike (~2–3 hrs code)
Python Script: Create a local test script evaluate_typos.py that takes 30 common customer support queries, injects common typos/slang, and runs them through score.py.
Outputs:
A CSV table (Original Message → Modified Message → Predicted Intent → Confidence → Match Y/N).
A FINDINGS.md summarizing if the TF-IDF model degrades completely on typos, determining if we need to implement spell-check preprocessing before vectorization.