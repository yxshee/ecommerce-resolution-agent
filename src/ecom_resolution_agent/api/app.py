from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi import Path as PathParam
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ecom_resolution_agent.api.frontend import render_dashboard_html
from ecom_resolution_agent.audit import RunArtifactWriter
from ecom_resolution_agent.config import get_settings
from ecom_resolution_agent.eval import (
    EvaluationHarness,
    EvaluationHarnessConfig,
    enforce_regression_thresholds,
    load_eval_scenarios,
    load_eval_thresholds,
    score_observations,
)
from ecom_resolution_agent.orchestration.pipeline import build_simulation_pipeline

# Run ids become directory names, so keep them to one plain path segment.
RUN_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$"


class CaseRunRequest(BaseModel):
    ticket: dict[str, Any]
    simulation: bool = True
    run_id: str | None = Field(default=None, pattern=RUN_ID_PATTERN)


class EvalRunRequest(BaseModel):
    # Resolved inside the datasets directory.
    dataset_path: str = "datasets/scenarios_v1.jsonl"
    thresholds_path: str = "datasets/eval_thresholds.json"
    # Resolved inside the artifacts directory.
    output_dir: str = "eval_api"
    limit: int | None = Field(default=None, ge=1)
    write_artifacts: bool = False


def _artifacts_root_dir() -> Path:
    base = os.environ.get("ECOM_ARTIFACTS_DIR")
    if base:
        return Path(base)
    if os.environ.get("VERCEL"):
        return Path("/tmp/ecom_resolution_agent/artifacts")
    return Path("artifacts")


def _datasets_root_dir() -> Path:
    return Path(os.environ.get("ECOM_DATASETS_DIR", "datasets"))


def _resolve_inside(root: Path, requested: str, *, field: str) -> Path:
    """Resolve a client-supplied path and refuse anything outside ``root``.

    Relative paths are taken from the working directory first (so the
    documented ``datasets/...`` defaults keep working) and then from ``root``.
    """
    root = root.resolve()
    candidate = Path(requested)
    options = [candidate] if candidate.is_absolute() else [candidate, root / candidate]
    for option in options:
        resolved = option.resolve()
        if resolved.is_relative_to(root):
            return resolved
    raise HTTPException(
        status_code=400,
        detail=f"{field} must be inside {root.name}/",
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Ecommerce Resolution Agent API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.get("/", tags=["system"], response_class=HTMLResponse)
    def root() -> str:
        return render_dashboard_html()

    @app.get("/ui", tags=["system"], response_class=HTMLResponse)
    def ui() -> str:
        return render_dashboard_html()

    @app.get("/v1/meta", tags=["system"])
    def metadata() -> dict[str, Any]:
        return {
            "name": "ecommerce-resolution-agent",
            "status": "ok",
            "mode": "simulation-first",
            "docs_url": "/docs",
            "health_url": "/healthz",
            "run_case_endpoint": "/v1/cases/run",
            "eval_endpoint": "/v1/evals/run",
        }

    @app.get("/healthz", tags=["system"])
    def healthz() -> dict[str, str | bool]:
        return {
            "status": "ok",
            "app_env": settings.app_env,
            "simulation_mode": settings.simulation_mode,
        }

    @app.post("/v1/cases/run", tags=["cases"])
    def run_case(request: CaseRunRequest) -> dict[str, Any]:
        if not request.simulation:
            raise HTTPException(
                status_code=400,
                detail="Only simulation mode is enabled in this environment.",
            )
        pipeline = build_simulation_pipeline(
            artifact_writer=RunArtifactWriter(base_dir=_artifacts_root_dir() / "runs")
        )
        result = pipeline.run_case(
            ticket=request.ticket,
            simulation_mode=request.simulation,
            run_id=request.run_id,
        )
        return {
            "run_id": result.run_id,
            "status": "completed",
            "summary": result.summary(),
            "decision": result.decision.model_dump(mode="json"),
            "qa_result": result.qa_result.model_dump(mode="json"),
            "action_result": (
                result.action_result.model_dump(mode="json")
                if result.action_result is not None
                else None
            ),
            "artifact_dir": str(result.artifact_dir),
            "report_path": str(result.artifact_dir / "report.md"),
        }

    @app.get("/v1/cases/{run_id}", tags=["cases"])
    def get_case(
        run_id: str = PathParam(pattern=RUN_ID_PATTERN),
    ) -> dict[str, Any]:
        run_dir = _artifacts_root_dir() / "runs" / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        run_config = _read_json_if_exists(run_dir / "run_config.json")
        decision = _read_json_if_exists(run_dir / "decision.json")
        report_path = run_dir / "report.md"
        return {
            "run_id": run_id,
            "artifact_dir": str(run_dir),
            "run_config": run_config,
            "decision": decision,
            "report_path": str(report_path),
            "report_exists": report_path.exists(),
        }

    @app.get("/v1/cases/{run_id}/artifacts", tags=["cases"])
    def get_case_artifacts(
        run_id: str = PathParam(pattern=RUN_ID_PATTERN),
    ) -> dict[str, Any]:
        run_dir = _artifacts_root_dir() / "runs" / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
        files = sorted(
            [
                {
                    "name": path.name,
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                }
                for path in run_dir.iterdir()
                if path.is_file()
            ],
            key=lambda item: str(item["name"]),
        )
        return {
            "run_id": run_id,
            "artifact_dir": str(run_dir),
            "files": files,
        }

    @app.post("/v1/approvals/{approval_task_id}/grant", tags=["approvals"])
    def grant_approval(approval_task_id: str) -> dict[str, Any]:
        return {
            "approval_task_id": approval_task_id,
            "status": "not_implemented",
            "detail": "Demo API is simulation-first and does not persist approval workflows yet.",
        }

    @app.post("/v1/approvals/{approval_task_id}/reject", tags=["approvals"])
    def reject_approval(approval_task_id: str) -> dict[str, Any]:
        return {
            "approval_task_id": approval_task_id,
            "status": "not_implemented",
            "detail": "Demo API is simulation-first and does not persist approval workflows yet.",
        }

    @app.post("/v1/evals/run", tags=["eval"])
    def run_eval(request: EvalRunRequest) -> dict[str, Any]:
        datasets_root = _datasets_root_dir()
        dataset_path = _resolve_inside(datasets_root, request.dataset_path, field="dataset_path")
        thresholds_path = _resolve_inside(
            datasets_root, request.thresholds_path, field="thresholds_path"
        )
        output_dir = _resolve_inside(_artifacts_root_dir(), request.output_dir, field="output_dir")
        if not dataset_path.is_file():
            raise HTTPException(
                status_code=404, detail=f"Dataset not found: {request.dataset_path}"
            )
        if not thresholds_path.is_file():
            raise HTTPException(
                status_code=404, detail=f"Thresholds not found: {request.thresholds_path}"
            )

        scenarios = load_eval_scenarios(dataset_path)
        if request.limit is not None:
            scenarios = scenarios[: request.limit]
        harness = EvaluationHarness(
            EvaluationHarnessConfig(
                artifact_base_dir=(output_dir / "runs") if request.write_artifacts else None
            )
        )
        observations = [harness.run_scenario(scenario) for scenario in scenarios]
        summary = score_observations(observations)
        thresholds = load_eval_thresholds(thresholds_path)
        failures = enforce_regression_thresholds(summary=summary, thresholds=thresholds)

        output_dir.mkdir(parents=True, exist_ok=True)
        results_path = output_dir / "evaluation_results.json"
        payload = summary.to_json()
        payload["gate"] = {"passed": not failures, "failures": failures}
        payload["dataset"] = str(dataset_path)
        payload["thresholds"] = str(thresholds_path)
        results_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        return {
            "status": "completed" if not failures else "failed_gate",
            "scenario_count": summary.scenario_count,
            "metrics": summary.metrics,
            "gate": payload["gate"],
            "results_path": str(results_path),
        }

    return app


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {"value": raw}
    return raw


app = create_app()
