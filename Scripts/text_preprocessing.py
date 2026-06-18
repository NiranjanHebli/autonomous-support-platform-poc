import nltk
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import numpy as np
import scipy.sparse as sp
from sklearn.base import BaseEstimator, TransformerMixin

# Ensure nltk data is downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))
punctuation = set(string.punctuation)

def preprocess_text(text):
    if not isinstance(text, str):
        return []
        
    tokens = word_tokenize(text.lower())
    
    processed_tokens = []
    for token in tokens:
        # Remove punctuation-only tokens
        if all(char in punctuation for char in token):
            continue
            
        # Remove stop words
        if token in stop_words:
            continue
            
        # Apply lemmatization
        lemmatized = lemmatizer.lemmatize(token)
        processed_tokens.append(lemmatized)
        
    return processed_tokens

class BM25Transformer(BaseEstimator, TransformerMixin):
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b

    def fit(self, X, y=None):
        self.n_samples, self.n_features = X.shape
        # Ensure X is CSR format
        if not isinstance(X, sp.csr_matrix):
            X = sp.csr_matrix(X)
            
        # Document frequencies (df): number of docs containing each term
        df = np.bincount(X.indices, minlength=X.shape[1])
        
        # IDF formula (Robertson et al. standard BM25 IDF)
        self.idf_ = np.log((self.n_samples - df + 0.5) / (df + 0.5) + 1.0)
        
        # Average document length
        self.avg_dl = X.sum() / self.n_samples
        return self

    def transform(self, X, y=None):
        # Ensure X is CSR format
        if not isinstance(X, sp.csr_matrix):
            X = sp.csr_matrix(X)
        else:
            X = X.copy()
            
        # Document lengths
        dl = X.sum(axis=1).A1
        
        repeats = np.diff(X.indptr)
        dl_expanded = np.repeat(dl, repeats)
        
        idf_expanded = self.idf_[X.indices]
        
        tf = X.data
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (1 - self.b + self.b * (dl_expanded / self.avg_dl))
        
        # Calculate BM25 weight
        X.data = idf_expanded * (numerator / denominator)
        
        return X
