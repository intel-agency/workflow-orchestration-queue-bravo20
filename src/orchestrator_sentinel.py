"""
The Brain - Sentinel Orchestrator

Background polling engine for task discovery, claiming, and worker dispatch.
Implements the "Sentinel" component of the OS-APOW architecture.
"""

import asyncio
import logging
import signal
import sys
from typing import Any

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from src.models.work_item import WorkItem, WorkItemStatus
from src.queue.github_queue import GitHubQueue

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Sentinel configuration from environment variables."""

    # Required secrets
    github_token: str = ""  # GH_ORCHESTRATION_AGENT_TOKEN

    # Repository configuration
    github_repo: str = ""  # Target repository (owner/repo format)

    # Sentinel behavior
    sentinel_bot_login: str = "sentinel-bot"  # Bot account for assign-then-verify
    polling_interval: int = 60  # Seconds between polls
    heartbeat_interval: int = 300  # Seconds between heartbeat comments
    subprocess_timeout: int = 5700  # Max subprocess runtime (seconds)

    # Feature flags
    debug_mode: bool = False

    class Config:
        env_prefix = ""
        env_file = ".env"
        extra = "ignore"


settings = Settings()


class SentinelState(BaseModel):
    """Runtime state of the Sentinel orchestrator."""

    running: bool = False
    tasks_processed: int = 0
    tasks_succeeded: int = 0
    tasks_failed: int = 0
    current_task: WorkItem | None = None


class Sentinel:
    """
    The Brain - Orchestrates task discovery, claiming, and dispatch.

    Lifecycle:
    1. Polling Discovery - Query GitHub for queued tasks
    2. Task Claiming - Assign-then-verify pattern
    3. Environment Check - Provision worker environment
    4. Dispatch - Execute worker via shell-bridge
    5. Telemetry - Heartbeat comments and status updates
    6. Reset - Cleanup for next task
    """

    def __init__(self) -> None:
        self.state = SentinelState()
        self.queue: GitHubQueue | None = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """Initialize the Sentinel and validate configuration."""
        logger.info("Initializing Sentinel orchestrator...")

        # Validate required settings
        if not settings.github_token:
            raise ValueError("GITHUB_TOKEN is required for Sentinel operation")
        if not settings.github_repo:
            raise ValueError("GITHUB_REPO is required for Sentinel operation")

        # Initialize queue client
        self.queue = GitHubQueue(
            token=settings.github_token,
            repo=settings.github_repo,
            bot_login=settings.sentinel_bot_login,
        )

        logger.info(f"Target repository: {settings.github_repo}")
        logger.info(f"Polling interval: {settings.polling_interval}s")
        logger.info(f"Heartbeat interval: {settings.heartbeat_interval}s")

    async def start(self) -> None:
        """Start the main polling loop."""
        self.state.running = True
        logger.info("Sentinel started - beginning polling loop")

        try:
            while self.state.running and not self._shutdown_event.is_set():
                await self._poll_cycle()
                await asyncio.sleep(settings.polling_interval)
        except asyncio.CancelledError:
            logger.info("Polling loop cancelled")
        finally:
            await self.shutdown()

    async def _poll_cycle(self) -> None:
        """Execute a single polling cycle."""
        try:
            if not self.queue:
                logger.error("Queue not initialized")
                return

            # Fetch queued tasks
            tasks = await self.queue.fetch_queued()
            if not tasks:
                logger.debug("No queued tasks found")
                return

            logger.info(f"Found {len(tasks)} queued task(s)")

            # Process first available task
            task = tasks[0]
            await self._process_task(task)

        except Exception as e:
            logger.exception(f"Error in poll cycle: {e}")

    async def _process_task(self, task: WorkItem) -> None:
        """Process a single work item through the full lifecycle."""
        logger.info(f"Processing task #{task.issue_number}: {task.title}")

        self.state.current_task = task

        try:
            # Claim the task (assign-then-verify pattern)
            claimed = await self.queue.claim_task(task)
            if not claimed:
                logger.warning(f"Failed to claim task #{task.issue_number}")
                return

            # Update status to in-progress
            await self.queue.update_progress(task, WorkItemStatus.IN_PROGRESS)

            # TODO: Implement shell-bridge dispatch
            # - Execute devcontainer-opencode.sh up
            # - Execute devcontainer-opencode.sh prompt "{workflow}"
            # - Capture stdout/stderr to JSONL log
            # - Apply heartbeat telemetry

            logger.info(f"Task #{task.issue_number} dispatched to worker")

            # For now, mark as success (actual implementation in Phase 1)
            await self.queue.finish_task(task, WorkItemStatus.SUCCESS)
            self.state.tasks_succeeded += 1

        except Exception as e:
            logger.exception(f"Error processing task #{task.issue_number}: {e}")
            if self.queue:
                await self.queue.finish_task(task, WorkItemStatus.ERROR)
            self.state.tasks_failed += 1

        finally:
            self.state.tasks_processed += 1
            self.state.current_task = None

    async def shutdown(self) -> None:
        """Graceful shutdown handler."""
        logger.info("Shutting down Sentinel...")

        # Wait for current task to complete (with timeout)
        if self.state.current_task:
            logger.info("Waiting for current task to complete...")
            # TODO: Implement proper task cancellation with cleanup

        self.state.running = False
        logger.info(
            f"Sentinel shutdown complete - "
            f"Processed: {self.state.tasks_processed}, "
            f"Succeeded: {self.state.tasks_succeeded}, "
            f"Failed: {self.state.tasks_failed}"
        )

    def request_shutdown(self) -> None:
        """Request graceful shutdown."""
        logger.info("Shutdown requested")
        self._shutdown_event.set()


# Global sentinel instance
_sentinel: Sentinel | None = None


def _signal_handler(signum: int, frame: Any) -> None:
    """Handle shutdown signals (SIGTERM, SIGINT)."""
    logger.info(f"Received signal {signum}")
    if _sentinel:
        _sentinel.request_shutdown()


def main() -> None:
    """Entry point for the Sentinel orchestrator."""
    global _sentinel

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if settings.debug_mode else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("Starting OS-APOW Sentinel...")

    # Setup signal handlers
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    # Create and run sentinel
    _sentinel = Sentinel()

    try:
        asyncio.run(_run_sentinel())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")


async def _run_sentinel() -> None:
    """Async entry point for running the sentinel."""
    if not _sentinel:
        return

    await _sentinel.initialize()
    await _sentinel.start()


if __name__ == "__main__":
    main()
