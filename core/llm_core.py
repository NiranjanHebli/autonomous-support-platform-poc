"""
Centralized LLM logic. Isolates initialization and API calls from business logic.
"""

import time
from groq import Groq, RateLimitError
from core.utils import ensure_env
from core.config import GROQ_MODEL, EMBEDDING_MODEL

from langchain_groq import ChatGroq
from ragas.llms import LangchainLLMWrapper
from langchain_community.embeddings import HuggingFaceEmbeddings
from ragas.embeddings import LangchainEmbeddingsWrapper


def get_llm_client() -> Groq:
    """Returns a configured Groq client using the strict ensure_env utility."""
    api_key = ensure_env("GROQ_API_KEY")
    return Groq(api_key=api_key)


def generate_completion(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 400,
    temperature: float = 0.2,
) -> dict:
    """
    Standard generation call wrapper for Groq with automatic retry on rate limits (429).

    Returns:
        dict: containing "answer", "prompt_tokens", "completion_tokens", and "model".
    """
    client = get_llm_client()

    max_retries = 5
    base_delay = 5.0

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return {
                "answer": response.choices[0].message.content.strip(),
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "model": response.model,
            }
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise e
            # Wait with exponential backoff
            wait_time = base_delay * (2**attempt)
            time.sleep(wait_time)


def get_ragas_llm():
    """Build Ragas-compatible LLM wrapper using Groq."""
    api_key = ensure_env("GROQ_API_KEY")
    llm = ChatGroq(model=GROQ_MODEL, api_key=api_key, temperature=0.0)
    return LangchainLLMWrapper(llm)


def get_ragas_embeddings():
    """Build Ragas-compatible embeddings wrapper using local sentence-transformers."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return LangchainEmbeddingsWrapper(embeddings)
