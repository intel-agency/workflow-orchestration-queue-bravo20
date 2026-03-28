# OS-APOW System Architecture

> **Application:** OS-APOW (Orchestration System for AI-Powered Orchestration Workflows)
> **Repository:** intel-agency/workflow-orchestration-queue-bravo20

## Executive Summary

OS-APOW represents a paradigm shift from **Interactive AI Coding** to **Headless Agentic Orchestration**. Traditional AI developer tools require a human-in-the-loop to navigate files, provide context, and trigger executions. OS-APOW replaces this manual overhead with a persistent, event-driven infrastructure that transforms GitHub Issues into autonomous "Execution Orders" fulfilled by specialized AI agents.

The system is designed to be **Self-Bootstrapping** - the initial deployment is seeded from a template, and once active, the system uses its own orchestration capabilities to refine and extend itself.

---

## System-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SYSTEMS                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │   GitHub    │    │    LLM      │    │   Docker    │                      │
│  │   (Issues,  │    │  Provider   │    │   Engine    │                      │
│  │   Webhooks) │    │ (ZhipuAI)   │    │             │                      │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                      │
└─────────┼──────────────────┼──────────────────┼─────────────────────────────┘
          │                  │                  │
          ▼                  │                  │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OS-APOW ORCHESTRATION LAYER                         │
│                                                                              │
│  ┌──────────────────┐         ┌──────────────────┐                          │
│  │   THE EAR        │         │    THE STATE     │                          │
│  │   (Notifier)     │         │    (Queue)       │                          │
│  │                  │         │                  │                          │
│  │ • FastAPI        │◄───────►│ • GitHub Issues  │                          │
│  │ • Webhook Ingest │         │ • Labels         │                          │
│  │ • HMAC Validation│         │ • Assignees      │                          │
│  │ • Event Triage   │         │ • Milestones     │                          │
│  └────────┬─────────┘         └────────▲─────────┘                          │
│           │                            │                                     │
│           │         ┌──────────────────┴──────────────────┐                 │
│           │         │                                     │                 │
│           │         ▼                                     │                 │
│  ┌────────┴──────────────────┐                            │                 │
│  │      THE BRAIN            │                            │                 │
│  │      (Sentinel)           │                            │                 │
│  │                           │                            │                 │
│  │ • Polling Engine (60s)    │────────────────────────────┘                 │
│  │ • Task Claiming (Lock)    │                                              │
│  │ • Shell-Bridge Dispatch   │                                              │
│  │ • Heartbeat Telemetry     │                                              │
│  │ • Graceful Shutdown       │                                              │
│  └────────────┬──────────────┘                                              │
│               │                                                              │
└───────────────┼──────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKER EXECUTION LAYER                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        THE HANDS (Worker)                             │   │
│  │                                                                       │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐   │   │
│  │  │   DevContainer  │    │   opencode CLI  │    │   LLM Agent     │   │   │
│  │  │   (Isolated)    │───►│   (Runtime)     │───►│   (GLM-5)       │   │   │
│  │  │                 │    │                 │    │                 │   │   │
│  │  │ • 2 CPU / 4GB   │    │ • MCP Servers   │    │ • Code Gen      │   │   │
│  │  │ • Network Isol. │    │ • Instructions  │    │ • PR Creation   │   │   │
│  │  │ • Ephemeral Creds│   │ • Task Execution│   │ • Test Running  │   │   │
│  │  └─────────────────┘    └─────────────────┘    └─────────────────┘   │   │
│  │                                                                       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. The Ear (Work Event Notifier)

**Technology:** Python 3.12, FastAPI, Pydantic, uv

**Role:** Primary gateway for external stimuli and asynchronous triggers

**Responsibilities:**

| Responsibility | Description |
|---------------|-------------|
| **Secure Webhook Ingestion** | Hardened endpoint at `/webhooks/github` for issues, issue_comment, and pull_request events |
| **Cryptographic Verification** | HMAC SHA256 validation against `WEBHOOK_SECRET` - prevents prompt injection attacks |
| **Intelligent Event Triage** | Parses issue body/labels, maps payloads to unified WorkItem object |
| **Queue Initialization** | Applies `agent:queued` label via GitHub REST API to signal Sentinel |

**Key Implementation:**
```
POST /webhooks/github
├── Validate X-Hub-Signature-256 header
├── Parse GitHub event payload
├── Map to WorkItem (TaskType, status)
└── Call GitHub API: POST /repos/{owner}/{repo}/issues/{number}/labels
```

---

### 2. The State (Work Queue)

**Implementation:** Distributed state via GitHub Issues, Labels, Milestones

**Philosophy:** "Markdown as a Database" - provides world-class audit trail and transparency

**State Machine (Label Logic):**

```
┌──────────────┐
│ agent:queued │ ◄─── Initial state after webhook triage
└──────┬───────┘
       │ Sentinel claims task (assign-then-verify)
       ▼
┌───────────────────┐
│ agent:in-progress │ ◄─── Sentinel assigned, work executing
└──────┬────────────┘
       │
       ├──────────────────────┬──────────────────────┐
       ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌─────────────────┐
│agent:success │      │ agent:error  │      │agent:infra-failure│
└──────────────┘      └──────────────┘      └─────────────────┘
```

**Concurrency Control:**
- GitHub Assignees act as distributed lock
- **Assign-then-Verify Pattern:**
  1. Attempt to assign `SENTINEL_BOT_LOGIN` to issue
  2. Re-fetch issue via GET API
  3. Verify `SENTINEL_BOT_LOGIN` in assignees array
  4. Only then update labels and proceed

---

### 3. The Brain (Sentinel Orchestrator)

**Technology:** Python (Async), PowerShell Core, Docker CLI

**Role:** Persistent supervisor managing Worker lifecycle and mapping intent to shell commands

**Lifecycle:**

| Phase | Action | Detail |
|-------|--------|--------|
| **Polling Discovery** | Query GitHub API every 60s | `GET /repos/{owner}/{repo}/issues?labels=agent:queued&state=open` |
| **Auth Synchronization** | Run `scripts/gh-auth.ps1` | Ensures valid installation tokens |
| **Task Claiming** | Assign-then-verify | Prevents race conditions |
| **Environment Check** | `devcontainer-opencode.sh up` | Provisions Docker network/volumes |
| **Dispatch** | `devcontainer-opencode.sh prompt "{workflow}"` | Core execution trigger |
| **Telemetry** | Heartbeat comments every 5 min | Background asyncio coroutine |
| **Environment Reset** | Stop worker container | Prevents state bleed between tasks |

**Key Features:**
- **Jittered Exponential Backoff** on HTTP 403/429
- **Graceful Shutdown** on SIGTERM/SIGINT
- **Subprocess Timeout Safety Net** (5700s default)

---

### 4. The Hands (Opencode Worker)

**Technology:** opencode CLI, LLM Core (GLM-5), DevContainer

**Environment:** Isolated Docker DevContainer from template

**Capabilities:**

| Capability | Description |
|-----------|-------------|
| **Contextual Awareness** | Vector-indexed codebase view via `update-remote-indices.ps1` |
| **Instructional Logic** | Reads `.md` workflow modules from `/local_ai_instruction_modules/` |
| **Verification** | Runs local test suites before PR submission |
| **PR Generation** | Creates formatted Pull Requests linking to original issue |

---

## Architectural Decision Records (ADRs)

### ADR-07: Standardized Shell-Bridge Execution

**Decision:** Orchestrator interacts with agentic environment exclusively via `./scripts/devcontainer-opencode.sh`

**Rationale:**
- Existing shell infrastructure handles complex Docker logic (volume mounting, SSH-agent forwarding, port mapping)
- Re-implementing in Python would create maintenance burden and configuration drift
- Ensures perfect environment parity between AI and human developers

**Consequence:** Python code remains lightweight (logic/state); Shell scripts handle infrastructure

---

### ADR-08: Polling-First Resiliency Model

**Decision:** Sentinel uses polling as primary discovery; Webhooks are optimization

**Rationale:**
- Webhooks are "fire and forget" - events lost if server is down
- Polling enables "State Reconciliation" on every restart
- System is inherently self-healing against downtime/network partitions

---

### ADR-09: Provider-Agnostic Interface Layer

**Decision:** All queue interactions abstracted behind `ITaskQueue` interface (Strategy Pattern)

**Rationale:**
- Phase 1 built for GitHub, but architecture designed for "Ticket Provider Swapping"
- Interface includes: `fetch_queued()`, `claim_task()`, `update_progress()`, `finish_task()`
- Enables future support for Linear, Notion, internal SQL queues without rewrite

---

## Data Flow (Happy Path)

```
1. STIMULUS: User opens GitHub Issue with application-plan.md template
       │
       ▼
2. NOTIFICATION: GitHub Webhook hits Notifier (FastAPI)
       │
       ▼
3. TRIAGE: Notifier validates signature, confirms template, adds agent:queued label
       │
       ▼
4. CLAIM: Sentinel poller detects label, assigns issue to Agent, updates to agent:in-progress
       │
       ▼
5. SYNC: Sentinel runs git clone/pull on target repo
       │
       ▼
6. ENVIRONMENT CHECK: Sentinel executes devcontainer-opencode.sh up
       │
       ▼
7. DISPATCH: Sentinel sends prompt command with workflow instruction
       │
       ▼
8. EXECUTION: Worker (opencode) reads issue, generates code, creates PR
       │
       ▼
9. FINALIZE: Worker posts completion comment, Sentinel applies agent:success label
```

---

## Security Architecture

### Network Isolation

```
┌─────────────────────────────────────────────────────────────┐
│                     Host Network                            │
│  ┌─────────────┐    ┌─────────────┐                        │
│  │  Sentinel   │    │   Notifier  │                        │
│  │  (Host)     │    │   (Host)    │                        │
│  └──────┬──────┘    └─────────────┘                        │
│         │                                                    │
│         │ Docker Bridge (isolated)                          │
│         ▼                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Worker Container                        │   │
│  │  • No access to host subnet                          │   │
│  │  • No access to AWS IMDS or peer containers          │   │
│  │  • Can reach internet for packages only              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Credential Flow

```
1. Sentinel generates ephemeral GitHub Installation Token
2. Token injected as in-memory environment variable
3. Worker container receives token (never written to disk)
4. Token destroyed on container exit
5. All logs scrubbed via scrub_secrets() before public visibility
```

### Credential Scrubbing Patterns

| Pattern | Example | Action |
|---------|---------|--------|
| GitHub PATs | `ghp_*`, `ghs_*`, `gho_*`, `github_pat_*` | Redact |
| Bearer tokens | `Bearer ...` | Redact |
| API keys | `sk-*`, ZhipuAI keys | Redact |

---

## Self-Bootstrapping Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│ Stage 0: Seeding                                                │
│ Developer manually clones template repository                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Manual Launch                                          │
│ Developer runs devcontainer-opencode.sh up                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Project Setup                                          │
│ orchestrate-project-setup workflow configures environment       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: Handover                                               │
│ Sentinel.py started on host; developer interacts via GitHub     │
│ System builds remaining features using its own orchestration    │
└─────────────────────────────────────────────────────────────────┘
```

---

## References

- [OS-APOW Development Plan v4.2](./OS-APOW%20Development%20Plan%20v4.2.md)
- [OS-APOW Implementation Specification v1.2](./OS-APOW%20Implementation%20Specification%20v1.2.md)
- [OS-APOW Tech Stack](./tech-stack.md)
