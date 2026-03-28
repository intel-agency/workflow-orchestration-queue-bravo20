"""
Work Item models for OS-APOW task representation.

Defines the core data structures for representing work items that flow
through the orchestration system.
"""

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Types of tasks that can be orchestrated."""

    APPLICATION_PLAN = "application-plan"
    BUGFIX = "bugfix"
    FEATURE = "feature"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TEST = "test"
    UNKNOWN = "unknown"


class WorkItemStatus(str, Enum):
    """Status states for work items in the queue."""

    QUEUED = "queued"  # agent:queued
    IN_PROGRESS = "in-progress"  # agent:in-progress
    SUCCESS = "success"  # agent:success
    ERROR = "error"  # agent:error
    INFRA_FAILURE = "infra-failure"  # agent:infra-failure


class WorkItem(BaseModel):
    """
    Represents a work item (task) in the orchestration queue.

    Work items are primarily backed by GitHub Issues, with state managed
    through labels and assignees.
    """

    issue_number: int = Field(..., description="GitHub issue number")
    title: str = Field(..., description="Issue title")
    body: str = Field(default="", description="Issue body/description")
    task_type: TaskType = Field(default=TaskType.UNKNOWN, description="Detected task type")
    status: WorkItemStatus = Field(default=WorkItemStatus.QUEUED, description="Current status")
    labels: list[str] = Field(default_factory=list, description="GitHub labels")
    assignees: list[str] = Field(default_factory=list, description="GitHub assignees")
    author: str = Field(default="", description="Issue author")
    url: str = Field(default="", description="GitHub issue URL")

    # Metadata
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")

    # Orchestration metadata
    sentinel_id: str | None = Field(default=None, description="Correlation ID for tracking")
    workflow: str | None = Field(default=None, description="Detected workflow to execute")

    model_config = {
        "use_enum_values": True,
        "populate_by_name": True,
    }

    def has_label(self, label: str) -> bool:
        """Check if the work item has a specific label."""
        return label in self.labels

    def is_claimed(self) -> bool:
        """Check if the work item is currently claimed (has assignees)."""
        return len(self.assignees) > 0

    def detect_task_type(self) -> TaskType:
        """
        Detect task type from issue body and labels.

        Template detection patterns:
        - [Application Plan] -> APPLICATION_PLAN
        - [Bugfix] -> BUGFIX
        - [Feature] -> FEATURE
        - [Refactor] -> REFACTOR
        - [Documentation] -> DOCUMENTATION
        - [Test] -> TEST
        """
        body_lower = self.body.lower()

        # Template markers in body
        template_patterns = {
            TaskType.APPLICATION_PLAN: r"\[application\s*plan\]",
            TaskType.BUGFIX: r"\[bugfix\]",
            TaskType.FEATURE: r"\[feature\]",
            TaskType.REFACTOR: r"\[refactor\]",
            TaskType.DOCUMENTATION: r"\[documentation\]",
            TaskType.TEST: r"\[test\]",
        }

        for task_type, pattern in template_patterns.items():
            if re.search(pattern, body_lower):
                return task_type

        # Label-based detection
        label_mappings = {
            "bug": TaskType.BUGFIX,
            "enhancement": TaskType.FEATURE,
            "documentation": TaskType.DOCUMENTATION,
            "refactor": TaskType.REFACTOR,
            "test": TaskType.TEST,
        }

        for label in self.labels:
            label_lower = label.lower()
            for pattern, task_type in label_mappings.items():
                if pattern in label_lower:
                    return task_type

        return TaskType.UNKNOWN

    def to_github_labels(self) -> list[str]:
        """Convert current status to GitHub label format."""
        return [f"agent:{self.status}"]


class WorkItemCreate(BaseModel):
    """Model for creating a new work item."""

    issue_number: int
    title: str
    body: str = ""
    labels: list[str] = Field(default_factory=list)
    author: str = ""
    url: str = ""


class WorkItemUpdate(BaseModel):
    """Model for updating a work item's status."""

    status: WorkItemStatus
    labels_to_add: list[str] = Field(default_factory=list)
    labels_to_remove: list[str] = Field(default_factory=list)
    comment: str | None = None


# Export all models
__all__ = [
    "TaskType",
    "WorkItemStatus",
    "WorkItem",
    "WorkItemCreate",
    "WorkItemUpdate",
]
