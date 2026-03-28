# OS-APOW

> **Orchestration System for AI-Powered Orchestration Workflows**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Overview

OS-APOW is a **headless agentic orchestration platform** that transforms GitHub Issues into autonomous AI-driven development workflows. It shifts AI from a passive co-pilot to an autonomous background production service—acting as a tireless junior developer that clones repositories, configures environments, generates code, runs tests, and submits Pull Requests without human intervention.

## Architecture

The system is built on **four pillars**:

| Pillar | Name | Technology | Purpose |
|--------|------|------------|---------|
| 1 | **The Ear** | FastAPI | Secure webhook ingestion with HMAC validation |
| 2 | **The State** | GitHub Issues | Distributed state via "Markdown as a Database" |
| 3 | **The Brain** | Python Async | Sentinel orchestrator with polling engine |
| 4 | **The Hands** | DevContainer + opencode | Isolated worker environment with LLM agent |

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for DevContainer worker)
- GitHub Personal Access Token with `repo`, `workflow`, `project`, `read:org` scopes

### Installation

```bash
# Clone the repository
git clone https://github.com/intel-agency/workflow-orchestration-queue-bravo20.git
cd workflow-orchestration-queue-bravo20

# Install dependencies with uv
uv sync

# Copy environment template
cp .env.example .env
# Edit .env with your credentials

# Run the notifier service
uv run uvicorn src.notifier_service:app --reload

# Run the sentinel orchestrator (separate terminal)
uv run python -m src.orchestrator_sentinel
```

### Docker

```bash
# Build the application image
docker build -t os-apow .

# Run with docker-compose
docker compose up -d
```

## Project Structure

```
workflow-orchestration-queue/
├── pyproject.toml               # Dependencies and tool configuration
├── Dockerfile                   # Application container
├── docker-compose.yml           # Local development stack
├── src/
│   ├── __init__.py
│   ├── notifier_service.py      # The Ear - FastAPI webhook receiver
│   ├── orchestrator_sentinel.py # The Brain - Polling engine
│   ├── models/
│   │   ├── work_item.py         # WorkItem, TaskType, WorkItemStatus
│   │   └── github_events.py     # GitHub webhook payload schemas
│   ├── queue/
│   │   └── github_queue.py      # ITaskQueue ABC + GitHubQueue
│   └── utils/
│       └── secret_scrubber.py   # Credential redaction utility
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── docs/                        # Architecture and user docs
├── scripts/                     # Shell/PowerShell utilities
└── .devcontainer/               # DevContainer configuration
```

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GH_ORCHESTRATION_AGENT_TOKEN` | GitHub PAT with repo, workflow, project scopes |
| `ZHIPU_API_KEY` | ZhipuAI API key for GLM models |
| `GITHUB_REPO` | Target repository (owner/repo format) |
| `WEBHOOK_SECRET` | HMAC secret for webhook validation |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `POLLING_INTERVAL` | 60 | Seconds between poll cycles |
| `HEARTBEAT_INTERVAL` | 300 | Seconds between heartbeat comments |
| `SENTINEL_BOT_LOGIN` | sentinel-bot | Bot account for task locking |
| `DEBUG_MODE` | false | Enable debug logging |

## API Documentation

When the notifier service is running, access the auto-generated API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_work_item.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type check
uv run mypy src/
```

## State Machine

Work items progress through the following states:

```
┌──────────────┐
│ agent:queued │ ◄─── Initial state
└──────┬───────┘
       │ Claim task
       ▼
┌───────────────────┐
│ agent:in-progress │
└──────┬────────────┘
       │
       ├──────────────┬──────────────────┐
       ▼              ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌─────────────────┐
│agent:success │ │ agent:error  │ │agent:infra-fail │
└──────────────┘ └──────────────┘ └─────────────────┘
```

## Security

- **HMAC Validation**: All webhooks validated with SHA256 signature
- **Credential Scrubbing**: Automatic redaction of secrets from logs/comments
- **Network Isolation**: Worker containers in segregated Docker network
- **Ephemeral Credentials**: Tokens injected as in-memory env vars, never written to disk

## References

- [Tech Stack Documentation](plan_docs/tech-stack.md)
- [Architecture Documentation](plan_docs/architecture.md)
- [Development Plan](plan_docs/OS-APOW%20Development%20Plan%20v4.2.md)
- [Implementation Specification](plan_docs/OS-APOW%20Implementation%20Specification%20v1.2.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
