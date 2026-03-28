"""
Queue management module for OS-APOW.

Provides the provider-agnostic ITaskQueue interface and GitHub implementation.
"""

from src.queue.github_queue import GitHubQueue, ITaskQueue

__all__ = [
    "ITaskQueue",
    "GitHubQueue",
]
