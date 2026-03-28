"""
Unit tests for secret scrubbing functionality.
"""

import pytest

from src.utils.secret_scrubber import scrub_dict, scrub_secrets


class TestScrubSecrets:
    """Tests for scrub_secrets function."""

    def test_scrub_github_pat(self) -> None:
        """Test scrubbing GitHub Personal Access Token."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxYZ12"
        result = scrub_secrets(text)

        assert "ghp_" not in result
        assert "[REDACTED_PAT]" in result

    def test_scrub_github_server_token(self) -> None:
        """Test scrubbing GitHub Server Token."""
        text = "Server token: ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        result = scrub_secrets(text)

        assert "ghs_" not in result
        assert "[REDACTED_PAT]" in result

    def test_scrub_bearer_token(self) -> None:
        """Test scrubbing Bearer token."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
        result = scrub_secrets(text)

        assert "Bearer eyJ" not in result
        assert "[REDACTED_BEARER]" in result

    def test_scrub_api_key(self) -> None:
        """Test scrubbing generic API key."""
        text = 'api_key="sk-1234567890abcdefghijklmnop"'
        result = scrub_secrets(text)

        assert "sk-1234" not in result
        assert "[REDACTED_API_KEY]" in result

    def test_scrub_no_secrets(self) -> None:
        """Test that non-secret text is unchanged."""
        text = "This is a regular log message without secrets"
        result = scrub_secrets(text)

        assert result == text

    def test_scrub_multiple_secrets(self) -> None:
        """Test scrubbing multiple secrets in one string."""
        text = "Token: ghp_abc123 and key=sk-xyz789"
        result = scrub_secrets(text)

        assert "ghp_" not in result
        assert "sk-" not in result
        assert "[REDACTED_PAT]" in result
        assert "[REDACTED_API_KEY]" in result


class TestScrubDict:
    """Tests for scrub_dict function."""

    def test_scrub_dict_token_key(self) -> None:
        """Test scrubbing dict with token key."""
        data = {"token": "secret-value", "name": "test"}
        result = scrub_dict(data)

        assert result["token"] == "[REDACTED]"
        assert result["name"] == "test"

    def test_scrub_dict_nested(self) -> None:
        """Test scrubbing nested dictionary."""
        data = {
            "config": {
                "api_key": "my-secret-key",
                "name": "test-config",
            },
            "count": 42,
        }
        result = scrub_dict(data)

        assert result["config"]["api_key"] == "[REDACTED]"
        assert result["config"]["name"] == "test-config"
        assert result["count"] == 42

    def test_scrub_dict_list_values(self) -> None:
        """Test scrubbing list values in dict."""
        data = {
            "items": ["ghp_abc123", "normal-value"],
            "count": 2,
        }
        result = scrub_dict(data)

        assert "ghp_" not in str(result["items"])
        assert "normal-value" in result["items"]

    def test_scrub_dict_secret_in_string(self) -> None:
        """Test scrubbing secrets within string values."""
        data = {"message": "Connected with token ghp_xyz123"}
        result = scrub_dict(data)

        assert "ghp_" not in result["message"]
        assert "[REDACTED_PAT]" in result["message"]

    def test_scrub_dict_password_key(self) -> None:
        """Test scrubbing dict with password key."""
        data = {"password": "super-secret", "username": "admin"}
        result = scrub_dict(data)

        assert result["password"] == "[REDACTED]"
        assert result["username"] == "admin"

    def test_scrub_dict_empty(self) -> None:
        """Test scrubbing empty dict."""
        data: dict = {}
        result = scrub_dict(data)

        assert result == {}
