TF-IDF Semantic Limitations
Likelihood: High | Impact: Medium
Mitigation: Re-train with a fallback sentence-transformer model if TF-IDF fails to catch synonyms/paraphrasing not present in the Bitext training data.
Social Media Rate Limiting
Likelihood: Medium | Impact: High
Mitigation: Implement exponential backoff in the Social Media client's send_message and get_messages functions.
Class Imbalance in Training Data
Likelihood: Medium | Impact: Medium
Mitigation: Use class_weight='balanced' in LightGBM if certain categories consistently underperform.
Out-of-Domain Gibberish Messages
Likelihood: High | Impact: Low
Mitigation: The 0.60 confidence threshold in score.py will catch most of these and safely default to 'UNDEFINED'.
Slow Social Media Room Joins
Likelihood: Low | Impact: Medium
Mitigation: Only call client.join_room when explicitly necessary or cache joined room states locally.
Riskiest Assumption: That TF-IDF vectorization will generalize well to actual user typos and slang. Because TF-IDF relies on exact word matches, user messages with severe typos (e.g., "pssword rset") might not trigger the correct LightGBM decision trees, unlike an embedding model which might capture the semantic closeness.