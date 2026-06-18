"""
Utility functions including strict environment variable management.
"""

import os
from dotenv import load_dotenv

# Ensure dotenv is loaded so env vars are available
load_dotenv()


def ensure_env(var_name: str, optional: bool = False) -> str:
    """
    Proactively checks if the requested environment variable exists and is not empty.

    If optional=False (default), it immediately throws a ValueError to prevent silent failures.
    If optional=True, it returns an empty string if missing.
    """
    val = os.getenv(var_name)
    if not val or not val.strip():
        if optional:
            return ""
        raise ValueError(
            f"Required environment variable '{var_name}' is missing or empty. "
            f"Please check your .env file."
        )
    return val.strip()
