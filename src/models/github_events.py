"""
GitHub webhook event models for OS-APOW.

Pydantic models for parsing and validating GitHub webhook payloads.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GitHubEventType(str, Enum):
    """Supported GitHub webhook event types."""

    ISSUES = "issues"
    ISSUE_COMMENT = "issue_comment"
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    PULL_REQUEST_REVIEW_COMMENT = "pull_request_review_comment"
    PUSH = "push"
    LABEL = "label"


class GitHubAction(str, Enum):
    """Common GitHub webhook actions."""

    # Issues
    OPENED = "opened"
    EDITED = "edited"
    CLOSED = "closed"
    REOPENED = "reopened"
    LABELED = "labeled"
    UNLABELED = "unlabeled"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"

    # Comments
    CREATED = "created"
    DELETED = "deleted"

    # Pull Requests
    SYNCHRONIZE = "synchronize"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_REQUEST_REMOVED = "review_request_removed"
    READY_FOR_REVIEW = "ready_for_review"
    CONVERTED_TO_DRAFT = "converted_to_draft"

    # Reviews
    SUBMITTED = "submitted"
    DISMISSED = "dismissed"


class GitHubUser(BaseModel):
    """GitHub user model."""

    login: str
    id: int
    node_id: str | None = None
    avatar_url: str | None = None
    type: str | None = None  # User, Bot, Organization


class GitHubLabel(BaseModel):
    """GitHub label model."""

    name: str
    id: int | None = None
    color: str | None = None
    description: str | None = None


class GitHubIssue(BaseModel):
    """GitHub issue model."""

    number: int
    title: str
    body: str | None = None
    state: str
    html_url: str
    user: GitHubUser | None = None
    labels: list[GitHubLabel] = Field(default_factory=list)
    assignees: list[GitHubUser] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    milestone: dict[str, Any] | None = None


class GitHubRepository(BaseModel):
    """GitHub repository model."""

    id: int
    name: str
    full_name: str
    owner: GitHubUser | None = None
    html_url: str | None = None
    private: bool = False


class GitHubEvent(BaseModel):
    """
    Unified GitHub webhook event model.

    Wraps the raw event payload with extracted metadata for easier processing.
    """

    event_type: str = Field(..., description="X-GitHub-Event header value")
    action: str | None = Field(default=None, description="Event action (if applicable)")
    payload: dict[str, Any] = Field(..., description="Raw event payload")

    # Extracted fields (populated from payload)
    issue: GitHubIssue | None = Field(default=None, description="Issue (if applicable)")
    repository: GitHubRepository | None = Field(default=None, description="Repository")
    sender: GitHubUser | None = Field(default=None, description="Event sender")
    label: GitHubLabel | None = Field(default=None, description="Label (for label events)")

    model_config = {
        "populate_by_name": True,
    }

    def model_post_init(self, __context: Any) -> None:
        """Extract common fields from payload after initialization."""
        # Extract repository
        if "repository" in self.payload:
            try:
                self.repository = GitHubRepository(**self.payload["repository"])
            except Exception:
                pass

        # Extract sender
        if "sender" in self.payload:
            try:
                self.sender = GitHubUser(**self.payload["sender"])
            except Exception:
                pass

        # Extract issue
        if "issue" in self.payload:
            try:
                self.issue = GitHubIssue(**self.payload["issue"])
            except Exception:
                pass

        # Extract label (for labeled/unlabeled events)
        if "label" in self.payload:
            try:
                self.label = GitHubLabel(**self.payload["label"])
            except Exception:
                pass

    @property
    def issue_number(self) -> int | None:
        """Get the issue number if this event relates to an issue."""
        if self.issue:
            return self.issue.number
        return None

    @property
    def repo_full_name(self) -> str | None:
        """Get the full repository name (owner/repo)."""
        if self.repository:
            return self.repository.full_name
        return None

    @property
    def is_bot_sender(self) -> bool:
        """Check if the event sender is a bot."""
        if self.sender:
            return self.sender.type == "Bot" or "[bot]" in self.sender.login
        return False

    def is_workflow_label(self) -> bool:
        """Check if this is a workflow-relevant label event."""
        if self.event_type != "issues" or self.action != "labeled":
            return False

        if not self.label:
            return False

        label_name = self.label.name
        return (
            label_name.startswith("orchestration:")
            or label_name == "implementation:ready"
            or label_name == "implementation:complete"
        )


class GitHubPullRequest(BaseModel):
    """GitHub pull request model."""

    number: int
    title: str
    body: str | None = None
    state: str
    html_url: str
    user: GitHubUser | None = None
    draft: bool = False
    merged: bool = False
    head: dict[str, Any] | None = None
    base: dict[str, Any] | None = None


class GitHubReview(BaseModel):
    """GitHub pull request review model."""

    id: int
    user: GitHubUser | None = None
    body: str | None = None
    state: str  # APPROVED, CHANGES_REQUESTED, COMMENTED, PENDING
    html_url: str | None = None


__all__ = [
    "GitHubEventType",
    "GitHubAction",
    "GitHubUser",
    "GitHubLabel",
    "GitHubIssue",
    "GitHubRepository",
    "GitHubEvent",
    "GitHubPullRequest",
    "GitHubReview",
]
