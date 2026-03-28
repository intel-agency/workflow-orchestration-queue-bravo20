---
file: AGENTS.md
description: Project instructions for coding agents
scope: repository
---

<instructions>
  <purpose>
    <summary>
      OS-APOW (Orchestration System for AI-Powered Orchestration Workflows) is a headless agentic orchestration
      platform that transforms GitHub Issues into autonomous AI-driven development workflows. The system receives
      GitHub webhooks, queues tasks via labels, and dispatches AI workers in isolated DevContainers to execute
      development tasks.
    </summary>
    <architecture>
      Four core pillars:
      - **The Ear (Notifier):** FastAPI webhook receiver with HMAC validation
      - **The State (Queue):** GitHub Issues + Labels as distributed task queue
      - **The Brain (Sentinel):** Polling orchestrator with task claiming
      - **The Hands (Worker):** opencode CLI + LLM agents in isolated containers
    </architecture>
  </purpose>

  <tech_stack>
    <item>Python 3.12+ — primary language for orchestrator, API, and system logic</item>
    <item>FastAPI — async web framework for webhook receiver (The Ear)</item>
    <item>Pydantic — data validation, settings management, schema definitions</item>
    <item>HTTPX — async HTTP client for GitHub REST API calls</item>
    <item>uv — Rust-based Python package manager (fast, deterministic)</item>
    <item>pytest — testing framework with async support</item>
    <item>ruff — fast linter and formatter (replaces flake8, black, isort)</item>
    <item>mypy — static type checking</item>
    <item>opencode CLI — AI agent runtime with MCP server support</item>
    <item>ZhipuAI GLM-5 — primary LLM model via `ZHIPU_API_KEY`</item>
    <item>Docker — worker container sandboxing, environment isolation</item>
    <item>MCP servers: `@modelcontextprotocol/server-sequential-thinking`, `@modelcontextprotocol/server-memory`</item>
  </tech_stack>

  <repository_map>
    <!-- Source Code -->
    <entry><path>src/notifier_service.py</path><description>FastAPI webhook receiver (The Ear) — HMAC validation, event triage, queue initialization</description></entry>
    <entry><path>src/orchestrator_sentinel.py</path><description>Polling orchestrator (The Brain) — task discovery, claiming, dispatch, telemetry</description></entry>
    <entry><path>src/models/work_item.py</path><description>Pydantic models: WorkItem, TaskType, WorkItemStatus</description></entry>
    <entry><path>src/models/github_events.py</path><description>GitHub webhook event schemas</description></entry>
    <entry><path>src/queue/github_queue.py</path><description>ITaskQueue interface + GitHubQueue implementation</description></entry>
    <entry><path>src/utils/secret_scrubber.py</path><description>Credential redaction utility for logs and comments</description></entry>
    <!-- Tests -->
    <entry><path>tests/unit/</path><description>Unit tests for core logic and utilities</description></entry>
    <entry><path>tests/integration/</path><description>Integration tests for API endpoints and queue operations</description></entry>
    <entry><path>tests/conftest.py</path><description>pytest fixtures and shared test configuration</description></entry>
    <!-- Configuration -->
    <entry><path>pyproject.toml</path><description>Python project configuration — dependencies, tool settings (ruff, mypy, pytest)</description></entry>
    <entry><path>uv.lock</path><description>Lockfile for deterministic dependency resolution</description></entry>
    <entry><path>Dockerfile</path><description>Application container definition</description></entry>
    <entry><path>docker-compose.yml</path><description>Local development stack configuration</description></entry>
    <!-- Scripts -->
    <entry><path>scripts/devcontainer-opencode.sh</path><description>Core shell-bridge for DevContainer + opencode execution</description></entry>
    <entry><path>scripts/gh-auth.ps1</path><description>GitHub authentication synchronization</description></entry>
    <entry><path>scripts/validate.ps1</path><description>Validation runner (lint, scan, test)</description></entry>
    <!-- Agent definitions -->
    <entry><path>.opencode/agents/orchestrator.md</path><description>Orchestrator — coordinates specialists, never writes code directly</description></entry>
    <entry><path>.opencode/agents/</path><description>All specialist agents (developer, code-reviewer, planner, devops-engineer, github-expert, etc.)</description></entry>
    <entry><path>.opencode/commands/</path><description>Reusable command prompts (orchestrate-new-project, grind-pr-reviews, fix-failing-workflows, etc.)</description></entry>
    <entry><path>.opencode/opencode.json</path><description>opencode config — MCP server definitions</description></entry>
    <!-- Devcontainer -->
    <entry><path>.devcontainer/devcontainer.json</path><description>Consumer devcontainer — pulls prebuilt GHCR image, forwards port 4096, auto-starts `opencode serve`</description></entry>
    <entry><path>scripts/start-opencode-server.sh</path><description>Guarded `opencode serve` bootstrapper</description></entry>
    <!-- Workflows -->
    <entry><path>.github/workflows/orchestrator-agent.yml</path><description>Primary workflow — assembles prompt, logs into GHCR, runs opencode in devcontainer</description></entry>
    <entry><path>.github/workflows/prompts/orchestrator-agent-prompt.md</path><description>Prompt template with `__EVENT_DATA__` placeholder</description></entry>
    <!-- Documentation -->
    <entry><path>plan_docs/</path><description>Project planning documents (architecture, tech stack, implementation specs)</description></entry>
    <entry><path>.ai-repository-summary.md</path><description>Auto-generated repository summary for AI agents</description></entry>
    <!-- Remote instructions -->
    <entry><path>local_ai_instruction_modules/</path><description>Local instruction modules (development rules, workflows, delegation, terminal commands)</description></entry>
  </repository_map>

  <instruction_source>
    <repository>
      <name>nam20485/agent-instructions</name>
      <branch>main</branch>
    </repository>
    <guidance>
      Remote instructions are the single source of truth. Fetch from raw URLs:
      replace `github.com/` with `raw.githubusercontent.com/` and remove `blob/`.
      Core instructions: `https://raw.githubusercontent.com/nam20485/agent-instructions/main/ai_instruction_modules/ai-core-instructions.md`
    </guidance>
    <modules>
      <module type="core" required="true" link="https://github.com/nam20485/agent-instructions/blob/main/ai_instruction_modules/ai-core-instructions.md">Core Instructions</module>
      <module type="local" required="true" path="local_ai_instruction_modules">Local AI Instructions</module>
      <module type="local" required="true" path="local_ai_instruction_modules/ai-dynamic-workflows.md">Dynamic Workflow Orchestration</module>
      <module type="local" required="true" path="local_ai_instruction_modules/ai-workflow-assignments.md">Workflow Assignments</module>
      <module type="local" required="true" path="local_ai_instruction_modules/ai-development-instructions.md">Development Instructions</module>
      <module type="optional" path="local_ai_instruction_modules/ai-terminal-commands.md">Terminal Commands</module>
    </modules>
  </instruction_source>

  <environment_setup>
    <secrets>
      <item>`ZHIPU_API_KEY` — ZhipuAI model access; set in repo Settings → Secrets.</item>
      <item>`KIMI_CODE_ORCHESTRATOR_AGENT_API_KEY` — Kimi (Moonshot) model access; set in repo Settings → Secrets.</item>
      <item>`GH_ORCHESTRATION_AGENT_TOKEN` — org-level PAT with scopes: repo, workflow, project, read:org. Required for orchestrator execution. No fallback to `GITHUB_TOKEN`.</item>
      <item>`GITHUB_TOKEN` — provided automatically by Actions; used only for GHCR login (image pull).</item>
      <item>`GITHUB_REPO` — Target repository for polling (format: owner/repo).</item>
      <item>`WEBHOOK_SECRET` — HMAC secret for webhook signature validation.</item>
      <item>`SENTINEL_BOT_LOGIN` — Bot account login for assign-then-verify locking.</item>
    </secrets>
    <optional_env>
      <item>`POLLING_INTERVAL` — Seconds between polls (default: 60).</item>
      <item>`HEARTBEAT_INTERVAL` — Seconds between heartbeat comments (default: 300).</item>
      <item>`SUBPROCESS_TIMEOUT` — Max subprocess runtime (default: 5700s).</item>
      <item>`DEBUG_MODE` — Enable debug logging (default: false).</item>
    </optional_env>
  </environment_setup>

  <testing>
    <guidance>Tests use pytest with async support. Run via `uv run pytest`.</guidance>
    <commands>
      <command>All tests: `uv run pytest`</command>
      <command>With coverage: `uv run pytest --cov=src --cov-report=term-missing`</command>
      <command>Unit tests only: `uv run pytest tests/unit/`</command>
      <command>Integration tests only: `uv run pytest tests/integration/`</command>
      <command>Specific test file: `uv run pytest tests/unit/test_work_item.py -v`</command>
      <command>With markers: `uv run pytest -m "not slow"`</command>
    </commands>
    <structure>
      <directory>tests/unit/</directory><description>Unit tests for models, utilities, and core logic</description>
      <directory>tests/integration/</directory><description>Integration tests for API endpoints and queue operations</directory>
      <file>tests/conftest.py</file><description>Shared fixtures and test configuration</description>
    </structure>
    <guidance>Add tests alongside new code. Maintain >80% coverage for core modules.</guidance>
  </testing>

  <coding_conventions>
    <rule>Keep changes minimal and targeted.</rule>
    <rule>Use Python 3.12+ features (type hints, pattern matching, f-strings).</rule>
    <rule>Do not hardcode secrets/tokens. When writing tests for credential-scrubbing or secret-detection utilities, use obviously synthetic values that will not trigger `gitleaks` (e.g., `FAKE-KEY-FOR-TESTING-00000000`). Never use prefixes that match real provider formats (`sk-`, `ghp_`, `ghs_`, `AKIA`, etc.) in test fixtures.</rule>
    <rule>Format code with ruff: `uv run ruff format .`</rule>
    <rule>Check linting with ruff: `uv run ruff check . --fix`</rule>
    <rule>Run type checking: `uv run mypy src/`</rule>
    <rule>Use Pydantic models for all data validation and settings.</rule>
    <rule>Use async/await for all I/O operations (HTTPX, file I/O, etc.).</rule>
    <rule>Preserve the `__EVENT_DATA__` placeholder in `orchestrator-agent-prompt.md`.</rule>
    <rule>Keep orchestrator delegation-depth ≤2 and "never write code directly" constraint.</rule>
    <rule>Pin ALL GitHub Actions by full SHA to the latest release — no tag or branch references (`@v4`, `@main`). Format: `uses: owner/action@<full-40-char-SHA> # vX.Y.Z`. The trailing comment with the semver tag is mandatory for human readability.</rule>
    <rule>Never add duplicate top-level `name:`, `on:`, or `jobs:` keys in workflow YAML.</rule>
    <rule>Repository labels are defined in `.github/.labels.json`. Use `scripts/import-labels.ps1` to sync them to a repo instance.</rule>
    <rule>Follow the 4-pillar architecture: Ear (Notifier), State (Queue), Brain (Sentinel), Hands (Worker).</rule>
    <rule>Use dependency injection via FastAPI's Depends() for testability.</rule>
  </coding_conventions>

  <!-- ═══════════════════════════════════════════════════════════════════
       MANDATORY TOOL PROTOCOLS — ALL AGENTS MUST FOLLOW
       These are NON-NEGOTIABLE requirements for every agent in this system.
       Failure to follow these protocols is a critical defect.
       ═══════════════════════════════════════════════════════════════════ -->
  <mandatory_tool_protocols>
    <overview>
      ALL agents — orchestrator, specialists, and subagents — MUST use the following
      MCP tools as part of their standard operating procedure. These are not optional
      suggestions; they are mandatory requirements that apply to every non-trivial task.
      Agents that skip these protocols are operating incorrectly.
    </overview>

    <protocol id="sequential_thinking" enforcement="MANDATORY">
      <title>Sequential Thinking Tool — ALWAYS USE</title>
      <tool>sequential_thinking</tool>
      <when>
        EVERY non-trivial task. This means any task that involves more than a single
        obvious action. If in doubt, use it.
      </when>
      <required_usage_points>
        <point>At task START: Use sequential thinking to analyze the request, break it into steps, identify risks, and plan the approach BEFORE taking any action.</point>
        <point>At DECISION POINTS: Use sequential thinking when choosing between alternatives, evaluating trade-offs, or making architectural decisions.</point>
        <point>When DEBUGGING: Use sequential thinking to systematically isolate root causes.</point>
        <point>Before DELEGATION: The Orchestrator MUST use sequential thinking to plan the delegation tree, determine agent assignments, and define success criteria.</point>
      </required_usage_points>
      <violation>Skipping sequential thinking on a non-trivial task is a protocol violation. If an agent completes a complex task without invoking sequential_thinking, the work should be reviewed for quality issues.</violation>
    </protocol>

    <protocol id="knowledge_graph_memory" enforcement="MANDATORY">
      <title>Knowledge Graph Memory — ALWAYS USE</title>
      <tools>
        <tool>create_entities</tool>
        <tool>create_relations</tool>
        <tool>add_observations</tool>
        <tool>delete_entities</tool>
        <tool>delete_observations</tool>
        <tool>delete_relations</tool>
        <tool>read_graph</tool>
        <tool>search_nodes</tool>
        <tool>open_nodes</tool>
      </tools>
      <required_usage_points>
        <point>At task START: Call `read_graph` or `search_nodes` to retrieve existing context about the project, user preferences, prior decisions, and known patterns BEFORE planning or acting.</point>
        <point>After SIGNIFICANT WORK: Call `create_entities`, `add_observations`, or `create_relations` to persist important findings, decisions, patterns discovered, and context for future tasks.</point>
        <point>After COMPLETING a task: Store the outcome, any lessons learned, and follow-up items in the knowledge graph.</point>
        <point>When STARTING a new workflow or assignment: Search for prior related work, decisions, and context.</point>
      </required_usage_points>
      <what_to_store>
        <item>Project-specific patterns and conventions discovered during work</item>
        <item>User preferences and decisions that affect future tasks</item>
        <item>Architectural decisions and their rationale</item>
        <item>Error patterns and their resolutions</item>
        <item>Cross-task context that would otherwise be lost between sessions</item>
        <item>Workflow state and progress checkpoints</item>
      </what_to_store>
      <violation>Failing to read existing memory at task start or failing to persist important findings after task completion is a protocol violation.</violation>
    </protocol>

    <protocol id="change_validation" enforcement="MANDATORY">
      <title>Change Validation Protocol — ALWAYS FOLLOW</title>
      <when>
        After ANY non-trivial change to code, configuration, workflows, or infrastructure.
        This includes: logic changes, behavior changes, refactors, dependency updates,
        config changes, multi-file edits, workflow modifications.
      </when>
      <required_steps>
        <step order="1">Install dependencies: `uv sync`</step>
        <step order="2">Run linting: `uv run ruff check . --fix`</step>
        <step order="3">Run formatting: `uv run ruff format .`</step>
        <step order="4">Run type checking: `uv run mypy src/`</step>
        <step order="5">Run tests: `uv run pytest`</step>
        <step order="6">Fix ALL failures — do not skip, suppress, or ignore errors.</step>
        <step order="7">Only THEN proceed to commit and push.</step>
      </required_steps>
      <validation_commands>
        <command purpose="install">uv sync</command>
        <command purpose="lint">uv run ruff check . --fix</command>
        <command purpose="format">uv run ruff format .</command>
        <command purpose="typecheck">uv run mypy src/</command>
        <command purpose="test">uv run pytest</command>
        <command purpose="all">uv sync && uv run ruff check . --fix && uv run ruff format . && uv run mypy src/ && uv run pytest</command>
      </validation_commands>
      <post_push>
        After push, monitor CI: `gh run list --limit 5`, `gh run watch &lt;id&gt;`, `gh run view &lt;id&gt; --log-failed`.
        If CI fails, STOP feature work, triage, fix, re-verify, push. Do NOT mark work complete while CI is red.
      </post_push>
      <violation>Committing or pushing code without running validation is a protocol violation. Marking a task complete while CI is failing is a protocol violation.</violation>
    </protocol>

    <agent_checklist>
      <!-- Agents: verify you have completed these items on every non-trivial task -->
      <item>☐ Called sequential_thinking at task start to plan approach</item>
      <item>☐ Called read_graph / search_nodes to retrieve prior context</item>
      <item>☐ Used sequential_thinking at key decision points during work</item>
      <item>☐ Ran validation (uv sync, ruff, mypy, pytest) before commit/push</item>
      <item>☐ Fixed all validation failures and re-verified clean</item>
      <item>☐ Persisted important findings to knowledge graph memory</item>
      <item>☐ Monitored CI after push and confirmed green</item>
    </agent_checklist>
  </mandatory_tool_protocols>

  <agent_specific_guardrails>
    <rule>The Orchestrator agent delegates to specialists via the `task` tool — never writes code directly.</rule>
    <rule>The Orchestrator MUST invoke `sequential_thinking` before planning any delegation and `read_graph` before every new task to load prior project context.</rule>
    <rule>ALL agents MUST follow the mandatory_tool_protocols defined above — sequential thinking, memory, and change validation are not optional.</rule>
    <rule>Prompt assembly pipeline:
      1. Read template from `.github/workflows/prompts/orchestrator-agent-prompt.md`.
      2. Prepend structured event context (event name, action, actor, repo, ref, SHA).
      3. Append raw event JSON from `${{ toJson(github.event) }}`.
      4. Write to `.assembled-orchestrator-prompt.md` and export path via `GITHUB_ENV`.
    </rule>
  </agent_specific_guardrails>

  <agent_readiness>
    <verification_protocol>
      MANDATORY: For any non-trivial change (logic, behavior, refactors, dependency updates, config changes, multi-file edits):
      run validation commands, fix all failures, re-run until clean. Do not skip or suppress errors.
      Do NOT commit or push until validation passes. Do NOT mark tasks complete while CI is red.
      See `mandatory_tool_protocols.change_validation` above for the full protocol.
    </verification_protocol>

    <verification_commands>
      <!--
        MANDATORY: After every non-trivial change, run validation BEFORE commit/push.
        Do NOT commit or push until it passes. Do NOT skip steps.

        | Check                  | Command                                | When to run              |
        |========================|========================================|==========================|
        | Install dependencies   | uv sync                                | After pyproject.toml change |
        | Lint code              | uv run ruff check . --fix              | Every task               |
        | Format code            | uv run ruff format .                   | Every task               |
        | Type check             | uv run mypy src/                       | After code changes       |
        | Run tests              | uv run pytest                          | After code changes       |
        | All checks             | uv sync && uv run ruff check . && uv run ruff format . && uv run mypy src/ && uv run pytest | Before commit |
      -->
      <rule>Run all validation commands before committing.</rule>
    </verification_commands>

    <post_commit_monitoring>
      After push, monitor CI until green: `gh run list --limit 5`, `gh run watch <id>`, `gh run view <id> --log-failed`.
      If any workflow fails, stop feature work, triage, fix, re-verify, push. Do not mark work complete while CI is failing.
    </post_commit_monitoring>

    <pipeline_speed_policy>
      <lane name="fast_readiness" blocking="true">Lint, format, type check, unit tests — keep fast for merge readiness.</lane>
      <lane name="extended_validation" blocking="false">Integration tests, security scans, dependency audits.</lane>
      <rule>Protect the fast lane from slow steps.</rule>
    </pipeline_speed_policy>
  </agent_readiness>

  <validation_before_handoff>
    <step>Run `uv sync` to ensure dependencies are installed.</step>
    <step>Run `uv run ruff check .` and `uv run ruff format .` for code quality.</step>
    <step>Run `uv run mypy src/` for type checking.</step>
    <step>Run `uv run pytest` to verify tests pass.</step>
    <step>Summarize: what changed, what was validated, remaining risks.</step>
  </validation_before_handoff>

  <tool_use_instructions>
    <instruction id="sequential_thinking_default_usage" enforcement="MANDATORY">
      <applyTo>*</applyTo>
      <title>Sequential Thinking — MANDATORY for all non-trivial tasks</title>
      <tools><tool>sequential_thinking</tool></tools>
      <guidance>
        **MUST USE** for all non-trivial requests. This is a mandatory protocol, not a suggestion.
        See `mandatory_tool_protocols.sequential_thinking` for full requirements.
        Invoke at: task start (planning), decision points, debugging, and before delegation.
        Skipping this tool on complex tasks is a protocol violation.
      </guidance>
    </instruction>
    <instruction id="memory_default_usage" enforcement="MANDATORY">
      <applyTo>*</applyTo>
      <title>Knowledge Graph Memory — MANDATORY for all non-trivial tasks</title>
      <tools><tool>create_entities</tool><tool>create_relations</tool><tool>add_observations</tool><tool>delete_entities</tool><tool>delete_observations</tool><tool>delete_relations</tool><tool>read_graph</tool><tool>search_nodes</tool><tool>open_nodes</tool></tools>
      <guidance>
        **MUST USE** for all non-trivial requests. This is a mandatory protocol, not a suggestion.
        See `mandatory_tool_protocols.knowledge_graph_memory` for full requirements.
        Invoke at: task start (read_graph/search_nodes), after significant work (create_entities/add_observations),
        and after task completion (persist outcomes and lessons learned).
        Skipping memory operations is a protocol violation.
      </guidance>
    </instruction>
  </tool_use_instructions>

  <available_tools>
    <summary>
      Tools available in the development environment. Python tools are installed via uv.
    </summary>

    <runtimes_and_package_managers>
      <tool name="python" version="3.12+">`Python` — primary language for orchestrator, API, and system logic.</tool>
      <tool name="uv" version="0.10+">`uv` — Rust-based Python package manager. Use `uv sync`, `uv run`, `uv add`.</tool>
      <tool name="node" version="24.14.0 LTS">`Node.js` — JavaScript runtime. Required for MCP server packages (`npx`).</tool>
      <tool name="bun" version="1.3.10">`Bun` — fast JavaScript/TypeScript runtime, bundler, and package manager.</tool>
    </runtimes_and_package_managers>

    <python_tools>
      <tool name="pytest">`pytest` — testing framework with async support. Run via `uv run pytest`.</tool>
      <tool name="ruff">`ruff` — fast linter and formatter. Run via `uv run ruff check .` and `uv run ruff format .`.</tool>
      <tool name="mypy">`mypy` — static type checker. Run via `uv run mypy src/`.</tool>
      <tool name="fastapi">`FastAPI` — async web framework for webhook receiver.</tool>
      <tool name="uvicorn">`Uvicorn` — ASGI server. Run via `uv run uvicorn src.notifier_service:app --reload`.</tool>
    </python_tools>

    <cli_tools>
      <tool name="gh">`GitHub CLI` — interact with GitHub API (issues, PRs, repos, releases, actions). Authenticated via `GH_ORCHESTRATION_AGENT_TOKEN` exported as `GH_TOKEN`.</tool>
      <tool name="opencode" version="1.2.24+">`opencode CLI` — AI agent runtime. Runs agents defined in `.opencode/agents/` with MCP server support.</tool>
      <tool name="git">`Git` — version control.</tool>
      <tool name="docker">`Docker` — container runtime for worker isolation.</tool>
    </cli_tools>

    <github_authentication>
      <summary>
        GitHub API access uses a single token: `GH_ORCHESTRATION_AGENT_TOKEN`, an org-level PAT
        with scopes `repo`, `workflow`, `project`, `read:org`. This token is required for
        orchestrator execution — there is no fallback to `GITHUB_TOKEN`.
      </summary>
      <layer name="GH_ORCHESTRATION_AGENT_TOKEN">Org-level PAT configured as a repo/org secret. Exported as `GH_TOKEN`, `GITHUB_TOKEN`, and `GITHUB_PERSONAL_ACCESS_TOKEN` so that `gh` CLI, MCP GitHub server, and opencode all authenticate with the same token.</layer>
      <layer name="GITHUB_TOKEN (Actions-provided)">Only used for GHCR login (`docker/login-action`) to pull devcontainer images. Not used for orchestrator API operations.</layer>
    </github_authentication>

    <scripts_directory>
      <summary>Shell and PowerShell helper scripts in `scripts/` for development and GitHub tasks.</summary>
      <script name="scripts/devcontainer-opencode.sh">Core shell-bridge for DevContainer + opencode execution.</script>
      <script name="scripts/gh-auth.ps1">GitHub authentication helper — syncs installation tokens.</script>
      <script name="scripts/validate.ps1">Validation runner — lint, scan, test.</script>
      <script name="scripts/import-labels.ps1">Imports labels from `.github/.labels.json` into the repository.</script>
      <script name="scripts/create-milestones.ps1">Creates project milestones from plan docs.</script>
      <script name="scripts/test-github-permissions.ps1">Verifies `GITHUB_TOKEN` has required permissions.</script>
      <script name="scripts/query.ps1">PR review thread manager — fetches and resolves review threads.</script>
      <script name="scripts/update-remote-indices.ps1">Updates remote instruction module indices.</script>
    </scripts_directory>
  </available_tools>

  <pr_commit_guidelines>
    <summary>
      Guidelines for creating Pull Requests and commits in this repository.
    </summary>
    <commit_message>
      <rule>Use conventional commit format: `type(scope): description`</rule>
      <rule>Types: feat, fix, docs, style, refactor, test, chore, ci</rule>
      <rule>Keep the first line under 72 characters</rule>
      <rule>Reference issues in the footer: `Closes #123` or `Relates to #456`</rule>
      <examples>
        <example>feat(notifier): add HMAC signature validation for webhooks</example>
        <example>fix(sentinel): correct assign-then-verify race condition</example>
        <example>docs(agents): update AGENTS.md with OS-APOW context</example>
        <example>test(queue): add unit tests for GitHubQueue.claim_task</example>
      </examples>
    </commit_message>
    <pull_requests>
      <rule>Link to the related issue in the PR description</rule>
      <rule>Include a summary of changes and testing performed</rule>
      <rule>Ensure all CI checks pass before requesting review</rule>
      <rule>Keep PRs focused — one logical change per PR</rule>
      <rule>Request review from relevant team members</rule>
    </pull_requests>
  </pr_commit_guidelines>
</instructions>
