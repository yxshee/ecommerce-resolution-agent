# Ecommerce Resolution Agent

Production-oriented, simulation-first multi-agent system for ecommerce support resolution with:

- LangGraph orchestration (intake through risk) plus deterministic post-risk pipeline stages
- Strict tool schemas and offline mock adapters
- Deterministic policy engine (versioned JSON)
- Risk scoring, approvals, action caps, and idempotency
- QA verification + prompt injection defense
- Reporting, ticket updates, and audit bundle artifacts
- Offline evaluation harness with regression gating
- CLI + FastAPI demo interfaces

## Quickstart

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Optional: Docker (Postgres/Redis local stack)

### Install

```bash
make install
```

### Run checks

```bash
make lint
make typecheck
make test
make eval
```

## One-Command Demo (Delivered But Not Received)

```bash
make demo_delivered_not_received
```

This runs the end-to-end simulation pipeline and prints a JSON summary including the `report.md` path.

Artifacts are written to:

- `artifacts/runs/<run_id>/run_config.json`
- `artifacts/runs/<run_id>/redacted_audit.jsonl`
- `artifacts/runs/<run_id>/decision.json`
- `artifacts/runs/<run_id>/report.md`

## CLI

### Run a case

```bash
uv run ecom-resolver run-case --ticket-file path/to/ticket.json --simulation
```

### Run a single step

```bash
uv run ecom-resolver run-step --state intake --input path/to/state.json
```

### Run evaluation harness

```bash
uv run ecom-resolver eval --output-dir artifacts/eval_cli
```

## API

### Run API server

```bash
uv run ecom-resolver api --host 127.0.0.1 --port 8000
```

### Key endpoints

- `GET /healthz`
- `POST /v1/cases/run`
- `GET /v1/cases/{run_id}`
- `GET /v1/cases/{run_id}/artifacts`
- `POST /v1/evals/run`
- `POST /v1/approvals/{approval_task_id}/grant` (demo stub)
- `POST /v1/approvals/{approval_task_id}/reject` (demo stub)

## CI

GitHub Actions runs:

- `lint`
- `typecheck`
- `unit_tests`
- `integration_mocks`
- `eval_regression`
- `db_migration_smoke`

## Notes

- Real actions remain disabled by default (`ENABLE_REAL_ACTIONS=false`).
- All local demos and evaluations run in simulation mode using mock tool adapters.
- Redaction is applied to audit logs/tool calls to reduce PII leakage risk.
