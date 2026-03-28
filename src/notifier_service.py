"""
The Ear - FastAPI Webhook Receiver

Secure endpoint for GitHub webhook ingestion with HMAC validation and event triaging.
Implements the "Notifier" component of the OS-APOW architecture.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from src.models.github_events import GitHubEvent
from src.queue.github_queue import GitHubQueue

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Required secrets
    github_token: str = ""  # GH_ORCHESTRATION_AGENT_TOKEN
    webhook_secret: str = ""  # WEBHOOK_SECRET for HMAC validation

    # Configuration
    github_repo: str = ""  # Target repository (owner/repo format)
    sentinel_bot_login: str = "sentinel-bot"  # Bot account for assign-then-verify

    # Feature flags
    debug_mode: bool = False

    class Config:
        env_prefix = ""
        env_file = ".env"
        extra = "ignore"


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    logger.info("OS-APOW Notifier starting up...")
    logger.info(f"Target repository: {settings.github_repo}")

    # Validate required settings
    if not settings.github_token:
        logger.warning("GITHUB_TOKEN not set - queue operations will fail")
    if not settings.webhook_secret:
        logger.warning("WEBHOOK_SECRET not set - HMAC validation disabled")

    yield

    logger.info("OS-APOW Notifier shutting down...")


app = FastAPI(
    title="OS-APOW Notifier",
    description="Webhook receiver for GitHub event ingestion",
    version="0.1.0",
    lifespan=lifespan,
)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning basic service info."""
    return {
        "service": "OS-APOW Notifier",
        "version": "0.1.0",
        "docs": "/docs",
    }


def verify_hmac_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    """
    Verify HMAC SHA256 signature from GitHub webhook.

    Args:
        payload: Raw request body bytes
        signature: Value of X-Hub-Signature-256 header
        secret: Shared secret for HMAC computation

    Returns:
        True if signature is valid, False otherwise
    """
    import hashlib
    import hmac

    if not signature or not secret:
        return False

    if not signature.startswith("sha256="):
        return False

    expected = signature[7:]  # Remove 'sha256=' prefix
    computed = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, computed)


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
) -> JSONResponse:
    """
    Handle GitHub webhook events.

    Validates HMAC signature, parses event payload, and queues work items.
    Returns 202 Accepted within GitHub's 10-second timeout requirement.
    """
    # Read raw body for signature verification
    payload = await request.body()

    # Verify HMAC signature (skip in debug mode)
    if not settings.debug_mode and settings.webhook_secret:
        if not verify_hmac_signature(payload, x_hub_signature_256, settings.webhook_secret):
            logger.warning("Invalid HMAC signature received")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    # Parse event
    if not x_github_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-GitHub-Event header",
        )

    try:
        event_data: dict[str, Any] = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from e

    # Create event model
    event = GitHubEvent(
        event_type=x_github_event,
        action=event_data.get("action"),
        payload=event_data,
    )

    logger.info(f"Received GitHub event: {event.event_type} (action={event.action})")

    # TODO: Implement event triaging and queue initialization
    # - Parse issue body for template detection
    # - Map to WorkItemType
    # - Apply agent:queued label via GitHubQueue

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"status": "accepted", "event_type": x_github_event},
    )


def main() -> None:
    """Entry point for the notifier service."""
    import uvicorn

    uvicorn.run(
        "src.notifier_service:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug_mode,
    )


if __name__ == "__main__":
    main()
