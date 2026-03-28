"""
GitHub Queue implementation for OS-APOW.

Implements the ITaskQueue interface using GitHub Issues as the backing store.
Follows the "Markdown as a Database" philosophy for distributed state.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import Self

import httpx

from src.models.work_item import WorkItem, WorkItemStatus

logger = logging.getLogger(__name__)


class ITaskQueue(ABC):
    """
    Provider-agnostic task queue interface.

    This abstraction enables future migration to other providers
    (Linear, Notion, internal SQL queues) without rewriting the orchestrator.
    """

    @abstractmethod
    async def fetch_queued(self) -> list[WorkItem]:
        """
        Fetch all work items in QUEUED status.

        Returns:
            List of work items ready to be processed.
        """
        ...

    @abstractmethod
    async def claim_task(self, work_item: WorkItem) -> bool:
        """
        Claim a work item for exclusive processing.

        Uses the assign-then-verify pattern to prevent race conditions
        in distributed scenarios.

        Args:
            work_item: The work item to claim.

        Returns:
            True if successfully claimed, False if already claimed by another.
        """
        ...

    @abstractmethod
    async def update_progress(self, work_item: WorkItem, status: WorkItemStatus) -> bool:
        """
        Update the status of a work item.

        Args:
            work_item: The work item to update.
            status: The new status.

        Returns:
            True if update succeeded.
        """
        ...

    @abstractmethod
    async def finish_task(self, work_item: WorkItem, status: WorkItemStatus) -> bool:
        """
        Mark a work item as finished with a terminal status.

        Args:
            work_item: The work item to finish.
            status: Terminal status (SUCCESS, ERROR, INFRA_FAILURE).

        Returns:
            True if update succeeded.
        """
        ...

    @abstractmethod
    async def add_comment(self, work_item: WorkItem, body: str) -> bool:
        """
        Add a comment to a work item.

        Used for heartbeat telemetry and status updates.

        Args:
            work_item: The work item to comment on.
            body: The comment body (markdown).

        Returns:
            True if comment was added successfully.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """
        Close the queue connection and release resources.

        Should be called during graceful shutdown.
        """
        ...


class GitHubQueue(ITaskQueue):
    """
    GitHub Issues-based task queue implementation.

    State Machine:
    - agent:queued → agent:in-progress → agent:success / agent:error / agent:infra-failure

    Concurrency Control:
    - Uses GitHub Assignees as distributed lock
    - Assign-then-verify pattern prevents race conditions
    """

    GITHUB_API_BASE = "https://api.github.com"

    def __init__(
        self,
        token: str,
        repo: str,
        bot_login: str = "sentinel-bot",
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """
        Initialize the GitHub queue.

        Args:
            token: GitHub Personal Access Token with repo scope.
            repo: Repository in owner/repo format.
            bot_login: Bot account login for assign-then-verify.
            http_client: Optional pre-configured HTTP client.
        """
        self.token = token
        self.repo = repo
        self.bot_login = bot_login
        self._client = http_client
        self._owns_client = http_client is None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.GITHUB_API_BASE,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Async context manager exit."""
        await self.close()

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        """
        Make an API request with jittered exponential backoff on rate limits.

        Args:
            method: HTTP method.
            path: API path.
            json: Request body.
            max_retries: Maximum retry attempts.

        Returns:
            HTTP response.

        Raises:
            httpx.HTTPStatusError: On non-retryable errors.
        """
        last_exception: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.request(method, path, json=json)

                # Handle rate limiting (403 with rate limit header)
                if response.status_code == 403 and "rate" in response.headers.get(
                    "x-ratelimit-remaining", "1"
                ):
                    if attempt < max_retries:
                        # Jittered exponential backoff: 2^attempt + random(0, 1) seconds
                        wait_time = (2**attempt) + random.random()
                        logger.warning(
                            f"Rate limited, retrying in {wait_time:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries + 1})"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code in (403, 429) and attempt < max_retries:
                    wait_time = (2**attempt) + random.random()
                    logger.warning(f"HTTP {e.response.status_code}, retrying in {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    continue
                raise

        raise last_exception or httpx.HTTPStatusError(
            "Max retries exceeded", request=None, response=None
        )  # type: ignore

    async def fetch_queued(self) -> list[WorkItem]:
        """
        Fetch all issues with agent:queued label.

        Returns:
            List of WorkItems in QUEUED status.
        """
        try:
            response = await self._request_with_retry(
                "GET",
                f"/repos/{self.repo}/issues",
                json={
                    "labels": "agent:queued",
                    "state": "open",
                    "per_page": 100,
                },
            )
            issues = response.json()

            work_items = []
            for issue in issues:
                work_item = WorkItem(
                    issue_number=issue["number"],
                    title=issue["title"],
                    body=issue.get("body", ""),
                    status=WorkItemStatus.QUEUED,
                    labels=[label["name"] for label in issue.get("labels", [])],
                    assignees=[a["login"] for a in issue.get("assignees", [])],
                    author=issue.get("user", {}).get("login", ""),
                    url=issue.get("html_url", ""),
                    created_at=issue.get("created_at"),
                    updated_at=issue.get("updated_at"),
                )
                work_items.append(work_item)

            return work_items

        except Exception as e:
            logger.exception(f"Failed to fetch queued issues: {e}")
            return []

    async def claim_task(self, work_item: WorkItem) -> bool:
        """
        Claim a work item using assign-then-verify pattern.

        1. Attempt to assign bot to issue
        2. Re-fetch issue
        3. Verify bot is in assignees

        Args:
            work_item: The work item to claim.

        Returns:
            True if successfully claimed.
        """
        try:
            # Step 1: Assign bot to issue
            await self._request_with_retry(
                "POST",
                f"/repos/{self.repo}/issues/{work_item.issue_number}/assignees",
                json={"assignees": [self.bot_login]},
            )

            # Step 2: Re-fetch to verify
            response = await self._request_with_retry(
                "GET",
                f"/repos/{self.repo}/issues/{work_item.issue_number}",
            )
            issue = response.json()

            # Step 3: Verify assignment
            assignees = [a["login"] for a in issue.get("assignees", [])]
            if self.bot_login in assignees:
                logger.info(f"Successfully claimed issue #{work_item.issue_number}")
                return True

            logger.warning(f"Failed to claim issue #{work_item.issue_number} - already assigned")
            return False

        except Exception as e:
            logger.exception(f"Error claiming issue #{work_item.issue_number}: {e}")
            return False

    async def update_progress(self, work_item: WorkItem, status: WorkItemStatus) -> bool:
        """
        Update work item status by managing labels.

        Removes agent:queued and adds the new status label.

        Args:
            work_item: The work item to update.
            status: The new status.

        Returns:
            True if update succeeded.
        """
        try:
            # Remove old status label
            await self._request_with_retry(
                "DELETE",
                f"/repos/{self.repo}/issues/{work_item.issue_number}/labels/agent:queued",
            )

            # Add new status label
            await self._request_with_retry(
                "POST",
                f"/repos/{self.repo}/issues/{work_item.issue_number}/labels",
                json={"labels": [f"agent:{status}"]},
            )

            logger.info(f"Updated issue #{work_item.issue_number} to {status}")
            return True

        except Exception as e:
            logger.exception(f"Error updating issue #{work_item.issue_number}: {e}")
            return False

    async def finish_task(self, work_item: WorkItem, status: WorkItemStatus) -> bool:
        """
        Mark a work item as finished.

        Removes agent:in-progress and adds terminal status label.

        Args:
            work_item: The work item to finish.
            status: Terminal status.

        Returns:
            True if update succeeded.
        """
        try:
            # Remove in-progress label
            await self._request_with_retry(
                "DELETE",
                f"/repos/{self.repo}/issues/{work_item.issue_number}/labels/agent:in-progress",
            )

            # Add terminal status label
            await self._request_with_retry(
                "POST",
                f"/repos/{self.repo}/issues/{work_item.issue_number}/labels",
                json={"labels": [f"agent:{status}"]},
            )

            logger.info(f"Finished issue #{work_item.issue_number} with status {status}")
            return True

        except Exception as e:
            logger.exception(f"Error finishing issue #{work_item.issue_number}: {e}")
            return False

    async def add_comment(self, work_item: WorkItem, body: str) -> bool:
        """
        Add a comment to the issue.

        Args:
            work_item: The work item to comment on.
            body: Comment body (markdown).

        Returns:
            True if comment was added.
        """
        try:
            await self._request_with_retry(
                "POST",
                f"/repos/{self.repo}/issues/{work_item.issue_number}/comments",
                json={"body": body},
            )

            logger.debug(f"Added comment to issue #{work_item.issue_number}")
            return True

        except Exception as e:
            logger.exception(f"Error adding comment to issue #{work_item.issue_number}: {e}")
            return False


__all__ = [
    "ITaskQueue",
    "GitHubQueue",
]
