# Typo Evaluation Findings

## Overview
Evaluated 30 common customer support queries by injecting deliberate typos to test the robustness of the TF-IDF vectorization and LightGBM model pipeline.

## Results
- **Total Queries**: 30
- **Matches (Intent maintained after typos)**: 5
- **Degradation Rate**: 83.3%

## Conclusion
The TF-IDF model degrades significantly on typos. We **do need** to implement spell-check preprocessing or subword tokenization (like character n-grams) before vectorization to maintain accuracy.

---

# Typo Evaluation Findings

## Overview
Evaluated 30 common customer support queries by injecting deliberate typos to test the robustness of the BM25 vectorization (with lemmatization) and LightGBM model pipeline.

## Results
- **Total Queries**: 30
- **Matches (Intent maintained after typos)**: 5
- **Degradation Rate**: 83.3%

## Conclusion
The BM25 + lemmatization model degrades significantly on typos. We **do need** to implement spell-check preprocessing or subword tokenization (like character n-grams) before vectorization to maintain accuracy.

---

# Typo Evaluation Findings

## Overview
Evaluated 30 common customer support queries by injecting deliberate typos, then applying TextBlob spell correction, to test the robustness of the BM25 vectorization (with lemmatization) and LightGBM model pipeline.

## Results
- **Total Queries**: 30
- **Matches (Intent maintained after typos + spell check)**: 19
- **Degradation Rate**: 36.7%

## Conclusion
Even with TextBlob spell correction, the model degrades significantly on typos. We might need a better spell checker or subword tokenization.
