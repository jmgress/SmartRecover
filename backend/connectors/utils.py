"""Utility functions for connectors."""

from typing import Any

from pydantic import SecretStr


def extract_secret_value(value: Any) -> str:
    """
    Extract the secret value from a SecretStr or return the value as-is.

    Args:
        value: Either a SecretStr instance, a regular string, or None

    Returns:
        The extracted secret value as a string, or empty string if value is None/falsy
    """
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    return value if value else ""
