"""
Unit tests for WorkItem model and related functionality.
"""

import pytest

from src.models.work_item import TaskType, WorkItem, WorkItemStatus


class TestWorkItemStatus:
    """Tests for WorkItemStatus enum."""

    def test_status_values(self) -> None:
        """Test that all expected status values exist."""
        assert WorkItemStatus.QUEUED == "queued"
        assert WorkItemStatus.IN_PROGRESS == "in-progress"
        assert WorkItemStatus.SUCCESS == "success"
        assert WorkItemStatus.ERROR == "error"
        assert WorkItemStatus.INFRA_FAILURE == "infra-failure"


class TestTaskType:
    """Tests for TaskType enum."""

    def test_task_type_values(self) -> None:
        """Test that all expected task types exist."""
        assert TaskType.APPLICATION_PLAN == "application-plan"
        assert TaskType.BUGFIX == "bugfix"
        assert TaskType.FEATURE == "feature"
        assert TaskType.REFACTOR == "refactor"
        assert TaskType.DOCUMENTATION == "documentation"
        assert TaskType.TEST == "test"
        assert TaskType.UNKNOWN == "unknown"


class TestWorkItem:
    """Tests for WorkItem model."""

    def test_work_item_creation(self, mock_github_issue: dict) -> None:
        """Test creating a WorkItem from GitHub issue data."""
        work_item = WorkItem(
            issue_number=mock_github_issue["number"],
            title=mock_github_issue["title"],
            body=mock_github_issue["body"],
            status=WorkItemStatus.QUEUED,
            labels=[label["name"] for label in mock_github_issue["labels"]],
            author=mock_github_issue["user"]["login"],
            url=mock_github_issue["html_url"],
        )

        assert work_item.issue_number == 42
        assert work_item.title == "Test Issue"
        assert work_item.status == WorkItemStatus.QUEUED
        assert "agent:queued" in work_item.labels

    def test_has_label_true(self) -> None:
        """Test has_label returns True when label exists."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            labels=["agent:queued", "bug"],
        )

        assert work_item.has_label("agent:queued") is True
        assert work_item.has_label("bug") is True

    def test_has_label_false(self) -> None:
        """Test has_label returns False when label doesn't exist."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            labels=["agent:queued"],
        )

        assert work_item.has_label("feature") is False

    def test_is_claimed_false(self) -> None:
        """Test is_claimed returns False when no assignees."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            assignees=[],
        )

        assert work_item.is_claimed() is False

    def test_is_claimed_true(self) -> None:
        """Test is_claimed returns True when assignees exist."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            assignees=["sentinel-bot"],
        )

        assert work_item.is_claimed() is True


class TestTaskTypeDetection:
    """Tests for task type detection from issue content."""

    def test_detect_application_plan(self) -> None:
        """Test detecting APPLICATION_PLAN from template marker."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            body="[Application Plan] Build a new feature",
        )

        detected = work_item.detect_task_type()
        assert detected == TaskType.APPLICATION_PLAN

    def test_detect_bugfix_from_body(self) -> None:
        """Test detecting BUGFIX from template marker."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            body="[Bugfix] Fix null pointer exception",
        )

        detected = work_item.detect_task_type()
        assert detected == TaskType.BUGFIX

    def test_detect_feature_from_body(self) -> None:
        """Test detecting FEATURE from template marker."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            body="[Feature] Add new endpoint",
        )

        detected = work_item.detect_task_type()
        assert detected == TaskType.FEATURE

    def test_detect_from_label(self) -> None:
        """Test detecting task type from label."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            body="Some description",
            labels=["bug", "priority:high"],
        )

        detected = work_item.detect_task_type()
        assert detected == TaskType.BUGFIX

    def test_detect_unknown(self) -> None:
        """Test returning UNKNOWN when no pattern matches."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            body="Just a regular issue",
            labels=["question"],
        )

        detected = work_item.detect_task_type()
        assert detected == TaskType.UNKNOWN

    def test_case_insensitive_detection(self) -> None:
        """Test that detection is case-insensitive."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            body="[APPLICATION PLAN] Lowercase test",
        )

        detected = work_item.detect_task_type()
        assert detected == TaskType.APPLICATION_PLAN


class TestWorkItemLabels:
    """Tests for label conversion."""

    def test_to_github_labels(self) -> None:
        """Test converting status to GitHub label format."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            status=WorkItemStatus.IN_PROGRESS,
        )

        labels = work_item.to_github_labels()
        assert labels == ["agent:in-progress"]

    def test_to_github_labels_success(self) -> None:
        """Test converting success status to GitHub label."""
        work_item = WorkItem(
            issue_number=1,
            title="Test",
            status=WorkItemStatus.SUCCESS,
        )

        labels = work_item.to_github_labels()
        assert labels == ["agent:success"]
