"""Core package for shared configurations, utilities, LLM logic, and prompts."""

import sys
from unittest.mock import MagicMock

# Monkeypatch for ragas 0.3.1 bug with langchain-community 0.4.x
if "langchain_community.chat_models.vertexai" not in sys.modules:
    sys.modules["langchain_community.chat_models.vertexai"] = MagicMock()
