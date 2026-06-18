"""
Centralized LLM logic. Isolates initialization and API calls from business logic.
"""

import time
from core.config import OLLAMA_MODEL, EMBEDDING_MODEL

from langchain_ollama import ChatOllama
from ragas.llms import LangchainLLMWrapper
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper


def generate_completion(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 400,
    temperature: float = 0.2,
) -> dict:
    """
    Standard generation call wrapper for Ollama.

    Returns:
        dict: containing "answer", "prompt_tokens", "completion_tokens", and "model".
    """
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=temperature,
        num_predict=max_tokens,
    )

    messages = [
        ("system", system_prompt),
        ("human", user_message),
    ]

    response = llm.invoke(messages)

    # Extract usage metrics if available, otherwise default to 0
    prompt_tokens = 0
    completion_tokens = 0
    if hasattr(response, "response_metadata") and response.response_metadata:
        prompt_tokens = response.response_metadata.get("prompt_eval_count", 0)
        completion_tokens = response.response_metadata.get("eval_count", 0)

    return {
        "answer": response.content.strip(),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "model": OLLAMA_MODEL,
    }


def get_ragas_llm():
    """Build Ragas-compatible LLM wrapper using Ollama (local, no rate limits)."""
    from langchain_ollama import ChatOllama

    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.0)
    return LangchainLLMWrapper(llm)


def get_ragas_embeddings():
    """Build Ragas-compatible embeddings wrapper using local sentence-transformers."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return LangchainEmbeddingsWrapper(embeddings)
