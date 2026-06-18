Problem + Cost: Customer support agents are spending ~30% of their time manually reading and triaging inbound Social Media messages to the correct department (e.g., Billing, Tech Support, Refunds). This manual triage costs approximately $4,500/month in agent hours and delays first-response times by an average of 45 minutes.

Top 3 User Stories:

As a customer, I want my support query to reach the correct department immediately so that my issue is resolved faster.
As a support agent, I want incoming Social Media messages to be pre-categorized so that I only see tickets relevant to my expertise.
As a support manager, I want to see a confidence score for automated routing so I can review low-confidence categorization.
Scope:

In Scope: Categorization of English text messages from Social Media; predicting Category and Intent; filtering out low-confidence (<0.60) predictions.
Out of Scope: Voice/audio message classification; automated ticket resolution (bot replies); multi-lingual support.
Requirements:

Functional: Model must predict Intent and Category from a text string. The pipeline must fallback to 'UNDEFINED' if confidence is below 0.60.
Non-functional: Inference latency under 200ms per message. Model must run locally without cloud GPU dependencies.
KPIs:

Macro F1-Score: Harmonic mean of precision and recall across all intents. Target: >0.85. Floor: 0.75.
Intent Match Rate: Percentage of messages where predicted intent exactly matches human labels. Target: >90%. Floor: 80%.
p95 Latency: Time to run text through TF-IDF and LightGBM inference. Target: <50ms. Floor: <200ms.
Automated Route Rate (Business KPI): Percentage of inbound Social Media messages successfully categorized (Confidence > 0.60) without human intervention. Target: >75%. Floor: 60%.