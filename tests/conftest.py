# Test configuration
"""
Pytest configuration and fixtures for OS-APOW tests.
"""

import asyncio
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_github_issue() -> dict[str, Any]:
    """Sample GitHub issue payload for testing."""
    return {
        "number": 42,
        "title": "Test Issue",
        "body": "## Test Issue\n\nThis is a test issue body.",
        "state": "open",
        "html_url": "https://github.com/test/repo/issues/42",
        "user": {
            "login": "testuser",
            "id": 12345,
        },
        "labels": [
            {"name": "agent:queued", "id": 1, "color": "blue"},
        ],
        "assignees": [],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_webhook_payload() -> dict[str, Any]:
    """Sample webhook payload for testing."""
    return {
        "action": "labeled",
        "issue": {
            "number": 42,
            "title": "Test Issue",
            "body": "[Application Plan] Test",
            "state": "open",
            "labels": [{"name": "orchestration:new-project"}],
        },
        "label": {"name": "orchestration:new-project"},
        "repository": {
            "full_name": "test/repo",
            "name": "repo",
            "owner": {"login": "test"},
        },
        "sender": {"login": "testuser", "type": "User"},
    }


@pytest.fixture
def mock_httpx_client() -> MagicMock:
    """Mock HTTPX async client."""
    client = MagicMock(spec=asyncio.AsyncMock)
    client.request = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock settings for testing."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-12345")
    monkeypatch.setenv("GITHUB_REPO", "test/repo")
    monkeypatch.setenv("WEBHOOK_SECRET", "test-secret")
    monkeypatch.setenv("DEBUG_MODE", "true")
