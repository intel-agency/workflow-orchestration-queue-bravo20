# OS-APOW Technology Stack

> **Application:** OS-APOW (Orchestration System for AI-Powered Orchestration Workflows)
> **Repository:** intel-agency/workflow-orchestration-queue-bravo20

## Overview

OS-APOW is a headless agentic orchestration platform that transforms GitHub Issues into autonomous AI-driven development workflows. The technology stack prioritizes async performance, security, and reproducibility.

---

## Languages & Runtimes

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Primary Language** | Python | 3.12+ | Orchestrator, API webhook receiver, system logic |
| **Shell Scripts** | Bash / PowerShell Core (pwsh) | Latest | Shell bridge execution, auth synchronization, CLI interactions |
| **LLM Runtime** | opencode CLI | 1.2.24+ | AI agent runtime with MCP server support |

---

## Frameworks & Libraries

### Core Frameworks

| Framework | Purpose |
|-----------|---------|
| **FastAPI** | High-performance async web framework for webhook receiver (The Ear). Native Pydantic integration, automatic OpenAPI generation. |
| **Uvicorn** | ASGI web server implementation for serving FastAPI in production |
| **Pydantic** | Strict data validation, settings management, schema definitions for WorkItem, TaskType, and cross-component communication |

### HTTP & Async

| Library | Purpose |
|---------|---------|
| **HTTPX** | Fully asynchronous HTTP client for non-blocking GitHub REST API calls. Connection pooling for efficiency. |

---

## Package Management

| Tool | Description |
|------|-------------|
| **uv** | Rust-based Python package installer and dependency resolver. Orders of magnitude faster than pip/poetry. Uses `pyproject.toml` and `uv.lock` for deterministic builds. |

---

## AI/LLM Integration

| Component | Provider | Model |
|-----------|----------|-------|
| **Primary LLM** | ZhipuAI | GLM-5 (zai-coding-plan/glm-5) |
| **Alternative** | Anthropic | Claude 3.5 Sonnet |
| **Agent Runtime** | opencode CLI | Supports multiple model providers via API keys |

### MCP Servers

| Server | Purpose |
|--------|---------|
| `@modelcontextprotocol/server-sequential-thinking` | Structured reasoning for complex tasks |
| `@modelcontextprotocol/server-memory` | Knowledge graph persistence |

---

## Containerization & Infrastructure

| Technology | Purpose |
|-----------|---------|
| **Docker** | Worker container sandboxing, environment consistency, lifecycle management |
| **DevContainers** | Reproducible development environment, bit-for-bit identical to production |
| **Docker Compose** | Multi-container orchestration for complex scenarios (e.g., web app + database) |

### Container Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Network Isolation** | Dedicated bridge network | Prevents lateral movement, isolates worker from host |
| **Resource Limits** | 2 CPUs, 4GB RAM | Prevents DoS from rogue agents |
| **Credential Handling** | Ephemeral environment variables | Never written to disk, destroyed on container exit |

---

## DevContainer Features

| Feature | Version | Purpose |
|---------|---------|---------|
| **Node.js** | 24.14.0 LTS | Required for MCP server packages (npx) |
| **.NET SDK** | 10.0.102 | Build, test, publish C#/F# projects |
| **Bun** | 1.3.10 | Fast JavaScript/TypeScript runtime and bundler |
| **uv** | 0.10.9 | Python package manager |
| **GitHub CLI (gh)** | Latest | GitHub API interactions |

---

## Data & State Management

| Component | Implementation | Purpose |
|-----------|---------------|---------|
| **Task Queue State** | GitHub Issues + Labels | "Markdown as a Database" - distributed state with world-class audit trail |
| **Locking Mechanism** | GitHub Assignees | Distributed semaphore for concurrency control |
| **Local Logs** | JSONL files | Worker output (Black Box) for forensic analysis |
| **Manifest Storage** | Shared volume / GitHub Issue metadata | Machine-readable WorkItem state |

---

## Security

| Feature | Implementation |
|---------|---------------|
| **Webhook Validation** | HMAC SHA256 signature verification (X-Hub-Signature-256) |
| **Credential Scoping** | GitHub App Installation Tokens with minimal scopes |
| **Credential Scrubbing** | Regex-based `scrub_secrets()` utility strips PATs, API keys, tokens |
| **Network Isolation** | Worker containers in segregated Docker network |

---

## Observability

| Component | Implementation |
|-----------|---------------|
| **Service Logging** | Python logging with StreamHandler, SENTINEL_ID correlation |
| **Public Telemetry** | Sanitized heartbeat comments on GitHub Issues (every 5 min) |
| **Container Logs** | Docker runtime capture (`docker logs`) |
| **API Documentation** | Auto-generated Swagger/OpenAPI at `/docs` |

---

## Testing

| Type | Framework | Target |
|------|-----------|--------|
| **Unit Tests** | pytest | Core logic, utilities |
| **Integration Tests** | pytest + httpx | API endpoints, queue operations |
| **Security Tests** | Custom | HMAC validation, credential scrubbing |

---

## Version Control & CI/CD

| Component | Tool |
|-----------|------|
| **Version Control** | Git |
| **Repository Hosting** | GitHub |
| **CI/CD** | GitHub Actions |
| **Branch Strategy** | main (production), develop (integration) |

---

## Environment Variables (Required)

| Variable | Purpose |
|----------|---------|
| `ZHIPU_API_KEY` | ZhipuAI model access |
| `KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY` | Kimi (Moonshot) model access |
| `GH_ORCHESTRATION_AGENT_TOKEN` | Org-level PAT (repo, workflow, project, read:org scopes) |
| `GITHUB_REPO` | Target repository for polling |
| `WEBHOOK_SECRET` | HMAC secret for webhook validation |
| `SENTINEL_BOT_LOGIN` | Bot account login for assign-then-verify locking |
| `SENTINEL_HEARTBEAT_INTERVAL` | Heartbeat comment interval (default: 300s) |
| `SUBPROCESS_TIMEOUT` | Max subprocess runtime (default: 5700s) |

---

## References

- [OS-APOW Development Plan v4.2](./OS-APOW%20Development%20Plan%20v4.2.md)
- [OS-APOW Architecture Guide v3.2](./OS-APOW%20Architecture%20Guide%20v3.2.md)
- [OS-APOW Implementation Specification v1.2](./OS-APOW%20Implementation%20Specification%20v1.2.md)
