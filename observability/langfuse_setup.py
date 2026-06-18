"""
Initialises the Langfuse client and returns the @observe decorator.

If LANGFUSE_PUBLIC_KEY is not set (e.g. in CI or local dev without tracing),
a no-op decorator is returned so the rest of the code works unchanged.

Environment variables required (add to .env):
    LANGFUSE_PUBLIC_KEY
    LANGFUSE_SECRET_KEY
    LANGFUSE_HOST  (default: https://cloud.langfuse.com)
"""

import functools
from core.utils import ensure_env


def _noop_observe(name: str = ""):
    """No-op decorator used when Langfuse is not configured."""

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_langfuse_decorator():
    """
    Returns the Langfuse @observe decorator if credentials are present,
    otherwise returns a transparent no-op decorator.
    """
    # Use optional=True so missing keys don't crash the app (graceful degradation)
    public_key = ensure_env("LANGFUSE_PUBLIC_KEY", optional=True)
    secret_key = ensure_env("LANGFUSE_SECRET_KEY", optional=True)
    host = ensure_env("LANGFUSE_HOST", optional=True) or "https://cloud.langfuse.com"

    if not public_key or not secret_key or public_key.startswith("pk-lf-your"):
        print(
            "[observability] Langfuse keys not configured — running without tracing.\n"
            "  Add LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY to .env to enable traces."
        )
        return _noop_observe

    try:
        from langfuse import observe
        from langfuse import Langfuse

        # Validate the connection on startup
        Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        print(f"[observability] Langfuse connected -> {host}")
        return observe
    except Exception as e:
        print(f"[observability] Langfuse init failed ({e}). Running without tracing.")
        return _noop_observe


def get_langfuse_client():
    """
    Returns an initialised Langfuse client for pulling metrics (Tier A).
    Returns None if not configured.
    """
    public_key = ensure_env("LANGFUSE_PUBLIC_KEY", optional=True)
    secret_key = ensure_env("LANGFUSE_SECRET_KEY", optional=True)
    host = ensure_env("LANGFUSE_HOST", optional=True) or "https://cloud.langfuse.com"

    if not public_key or not secret_key or public_key.startswith("pk-lf-your"):
        return None

    try:
        return Langfuse(public_key=public_key, secret_key=secret_key, host=host)
    except Exception:
        return None
