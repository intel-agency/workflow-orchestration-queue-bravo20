"""
Secret scrubbing utility for OS-APOW.

Provides functions to redact sensitive information from logs, comments,
and other public-facing output.
"""

import re
from typing import Any


# Patterns for detecting sensitive data
SECRET_PATTERNS = [
    # GitHub Personal Access Tokens
    (r"ghp_[a-zA-Z0-9]{36}", "ghp_[REDACTED]"),
    (r"ghs_[a-zA-Z0-9]{36}", "ghs_[REDACTED]"),
    (r"gho_[a-zA-Z0-9]{36}", "gho_[REDACTED]"),
    (r"ghu_[a-zA-Z0-9]{36}", "ghu_[REDACTED]"),
    (r"ghr_[a-zA-Z0-9]{36}", "ghr_[REDACTED]"),
    (r"github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}", "github_pat_[REDACTED]"),
    # Bearer tokens
    (r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", "Bearer [REDACTED]"),
    # OpenAI API keys
    (r"sk-[a-zA-Z0-9]{20}T3BlbkFJ[a-zA-Z0-9]{20}", "sk-[REDACTED]"),
    (r"sk-proj-[a-zA-Z0-9]{20}T3BlbkFJ[a-zA-Z0-9]{20}", "sk-proj-[REDACTED]"),
    # Anthropic API keys
    (r"sk-ant-[a-zA-Z0-9\-_]{80,}", "sk-ant-[REDACTED]"),
    # ZhipuAI API keys (example pattern - adjust based on actual format)
    (r"[a-f0-9]{32}\.[a-zA-Z0-9]{32}\.[a-zA-Z0-9\-_]{32,}", "[REDACTED_API_KEY]"),
    # Generic API key patterns
    (r"api[_-]?key[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9\-_]{20,}", "api_key=[REDACTED]"),
    (r"secret[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9\-_]{20,}", "secret=[REDACTED]"),
    (r"token[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9\-_]{20,}", "token=[REDACTED]"),
    # AWS credentials
    (r"AKIA[0-9A-Z]{16}", "AKIA[REDACTED]"),
    (
        r"aws[_-]?secret[_-]?access[_-]?key[\"']?\s*[:=]\s*[\"']?[a-zA-Z0-9/+=]{40}",
        "aws_secret_access_key=[REDACTED]",
    ),
    # Private keys
    (
        r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |DSA )?PRIVATE KEY-----",
        "[PRIVATE_KEY_REDACTED]",
    ),
]


def scrub_secrets(text: str) -> str:
    """
    Remove or redact sensitive information from text.

    This function is critical for preventing credential leaks in:
    - Log output
    - GitHub comments
    - Heartbeat telemetry
    - Error messages

    Args:
        text: The text to scrub.

    Returns:
        Text with secrets redacted.

    Example:
        >>> scrub_secrets("Token: ghp_1234567890abcdefghijklmnopqrstuvwxYZ12")
        'Token: ghp_[REDACTED]'
    """
    result = text

    for pattern, replacement in SECRET_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result


def scrub_dict(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively scrub secrets from a dictionary.

    Args:
        data: Dictionary to scrub.

    Returns:
        Dictionary with secrets redacted.
    """
    result: dict[str, Any] = {}

    for key, value in data.items():
        key_lower = key.lower()

        # Check if key name suggests sensitive data
        if any(
            sensitive in key_lower
            for sensitive in ["token", "secret", "key", "password", "credential"]
        ):
            result[key] = "[REDACTED]"
        elif isinstance(value, str):
            result[key] = scrub_secrets(value)
        elif isinstance(value, dict):
            result[key] = scrub_dict(value)
        elif isinstance(value, list):
            result[key] = [
                scrub_dict(item)
                if isinstance(item, dict)
                else scrub_secrets(item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value

    return result


__all__ = [
    "scrub_secrets",
    "scrub_dict",
]
