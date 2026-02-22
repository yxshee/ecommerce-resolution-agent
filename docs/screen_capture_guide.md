# Screen Capture Guide (Phase 10 Demo)

## Goal

Record a short local demo of the `delivered_not_received` simulation flow.

## Recommended Sequence

1. Run `make demo_delivered_not_received`
2. Show the CLI JSON output (includes `report_path`)
3. Open the generated `report.md`
4. Open `artifacts/runs/<run_id>/redacted_audit.jsonl`
5. Optionally run `uv run ecom-resolver eval --output-dir artifacts/eval_cli --limit 10`

## What To Highlight

- Simulation mode is enabled (no real actions)
- Selected resolution action
- Redacted audit entries
- Generated report artifact
- Deterministic, reproducible output paths

## API Demo (Optional)

1. Start server: `uv run ecom-resolver api`
2. Call `POST /v1/cases/run` from Swagger UI (`/docs`)
3. Call `GET /v1/cases/{run_id}/artifacts`

## Recording Tips

- Keep terminal font size readable
- Use a fresh terminal session for clarity
- Avoid showing secrets or unrelated files
