# Changelog

## 0.1.1 (2026-11-04)

### Fixed

- Running a mini evaluation from the deployed dashboard with "Write artifacts: yes" returned HTTP 500, because run folders were written under the read-only deployment directory. They now go under the artifacts directory, as the results file already did (#16).
- The API used file paths taken from the request: `/v1/evals/run` read datasets and wrote results at any path a client sent, and `/v1/cases/run` accepted a `run_id` containing `..`. Datasets and thresholds now have to come from `datasets/`, output stays under the artifacts directory, and a run id must be a single name (#17).

### Changed

- `EvalRunRequest.output_dir` now defaults to `eval_api` and is resolved inside the artifacts directory (`ECOM_ARTIFACTS_DIR`). Callers that sent an absolute `output_dir` should set `ECOM_ARTIFACTS_DIR` instead.
- The OpenAPI version now follows the package version.

## 0.1.0 (2026-11-02)

First tagged release.

### What's in it

- LangGraph `StateGraph` from intake through risk assessment, followed by a deterministic decision, QA, action and reporting pipeline.
- Versioned JSON policy engine (`policies/versions/v1_0_0/`), risk scoring, hard action caps, idempotency keys and a human approval gate. Real actions are off by default (`ENABLE_REAL_ACTIONS=false`).
- Prompt-injection checks on customer messages and PII redaction on audit logs and tool-call envelopes.
- 250-scenario offline evaluation harness with thresholds committed in `datasets/eval_thresholds.json`, enforced in CI.
- CLI (`ecom-resolver`), FastAPI service and a browser dashboard at `/`.
- Offline mock tool adapters: no API keys or network needed.

### Fixed in this release

- The dashboard was wider than the window at every screen size (about 1,440 px wide even on a 390 px phone), so the right-hand panels were cut off. Grid columns now shrink to fit, and only the pipeline strip scrolls sideways.

### Added in this release

- `LICENSE` file (MIT, as the README already stated), this changelog, a dashboard screenshot and a copy-paste quick start in the README.

### Known limits

- No live model calls: every agent role is a deterministic implementation behind the interface a model would use. See "Scope and honesty" in the README.
- All tickets, orders and customers are synthetic.
