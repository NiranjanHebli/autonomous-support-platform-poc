import sys
import os
from pathlib import Path

# Ensure the root directory is in the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Monkeypatch for deepeval bug with newer langchain versions
import langchain_core.messages

sys.modules["langchain.schema"] = sys.modules["langchain_core.messages"]

import pytest
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from deepeval import assert_test

from app.pipeline import run
from core.config import OLLAMA_MODEL


class OllamaDeepEval(DeepEvalBaseLLM):
    """Custom wrapper to use local Ollama with DeepEval"""

    def __init__(self):
        pass

    def load_model(self):
        # Model is loaded dynamically in generate
        return None

    def generate(self, prompt: str) -> str:
        from langchain_ollama import ChatOllama

        llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.0)
        response = llm.invoke(prompt)
        return response.content

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return OLLAMA_MODEL


def test_faithfulness_baseline():
    """
    Test the pipeline's faithfulness using DeepEval against the local Ollama model.
    Fails the build if faithfulness drops below the 0.90 floor.
    """
    # Use a solid, standard question from the domain
    question = "What is the policy for returning damaged items?"

    # 1. Run the RAG pipeline
    output = run(question, top_k=5)

    # Extract context strings
    retrieval_context = (
        output["contexts"]
        if isinstance(output["contexts"], list)
        else [output["contexts"]]
    )

    # 2. Define the DeepEval test case
    test_case = LLMTestCase(
        input=question,
        actual_output=output["answer"],
        retrieval_context=retrieval_context,
    )

    # 3. Define the metric with our local custom model
    # The week 16 target floor is 0.90
    custom_model = OllamaDeepEval()
    metric = FaithfulnessMetric(threshold=0.90, model=custom_model, include_reason=True)

    # 4. Assert the test
    assert_test(test_case, [metric])


if __name__ == "__main__":
    test_faithfulness_baseline()
    print("DeepEval faithfulness test passed!")
