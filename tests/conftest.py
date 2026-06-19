import sys

try:
    import langchain_core.messages

    sys.modules["langchain.schema"] = sys.modules["langchain_core.messages"]
except ImportError:
    pass
