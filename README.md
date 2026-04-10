# Ecommerce Resolution Agent

A production-oriented multi-agent system for resolving ecommerce customer issues with deterministic policies, safe tool execution, auditability, and offline evaluation.

## Phase 0 Status

This repository currently contains the bootstrap scaffolding for:

- Python package (`src/` layout)
- FastAPI API skeleton (`/healthz`)
- CLI skeleton (`ecom-resolver`)
- Ruff, MyPy, Pytest configuration
- GitHub Actions CI (lint, typecheck, tests)
- Docker Compose services for Postgres and Redis (for later phases)

## Quickstart

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Optional for later phases: Docker (Postgres + Redis local stack)

### Install

```bash
make install
```

### Run checks

```bash
make lint
make typecheck
make test
```

### CLI help

```bash
uv run python -m ecom_resolution_agent.cli --help
```

### Run API (health endpoint)

```bash
uv run ecom-resolver api --host 127.0.0.1 --port 8000
```

Then visit `http://127.0.0.1:8000/healthz`.

## Local infrastructure (later phases)

Docker is not required for Phase 0. When available, start local Postgres + Redis with:

```bash
docker compose up -d
```

## High-Level Architecture (target)

- `Triage Agent` -> classifies issues and requests missing data
- `Policy Agent` -> deterministic policy evaluation from versioned JSON rules
- `Risk Agent` -> fraud/risk scoring and approval gating
- `Actions Agent` -> simulation-first action execution with idempotency + caps
- `QA Agent` -> evidence/policy verification and prompt injection defense
- `Report Agent` -> customer response + internal audit/report artifacts
