from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ecom_resolution_agent.api.app import app


def test_root_returns_dashboard_html() -> None:
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "Ecommerce Resolution Agent" in body
    assert "Run Delivered-Not-Received Demo" in body
    assert "/v1/cases/run" in body


def test_meta_returns_service_metadata() -> None:
    client = TestClient(app)
    response = client.get("/v1/meta")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "ecommerce-resolution-agent"
    assert payload["status"] == "ok"
    assert payload["docs_url"] == "/docs"


def test_healthz_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/healthz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["simulation_mode"] is True


def test_case_run_and_artifact_endpoints_round_trip() -> None:
    client = TestClient(app)
    run_response = client.post(
        "/v1/cases/run",
        json={
            "ticket": {
                "ticket_id": "api_case_001",
                "customer_id": "cus_001",
                "order_id": "ord_001",
                "customer_email": "alice@example.com",
                "issue_type": "delivered_not_received",
                "customer_message": "Delivered but not received",
            },
            "simulation": True,
            "run_id": "api_case_run_001",
        },
    )

    assert run_response.status_code == 200
    run_payload = run_response.json()
    run_id = run_payload["run_id"]
    report_path = Path(run_payload["report_path"])
    assert report_path.exists()

    case_response = client.get(f"/v1/cases/{run_id}")
    assert case_response.status_code == 200
    case_payload = case_response.json()
    assert case_payload["run_id"] == run_id
    assert case_payload["report_exists"] is True

    artifacts_response = client.get(f"/v1/cases/{run_id}/artifacts")
    assert artifacts_response.status_code == 200
    files = {item["name"] for item in artifacts_response.json()["files"]}
    assert {"run_config.json", "redacted_audit.jsonl", "decision.json", "report.md"} <= files


def test_eval_run_endpoint_supports_limited_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ECOM_ARTIFACTS_DIR", str(tmp_path))
    client = TestClient(app)
    response = client.post(
        "/v1/evals/run",
        json={
            "output_dir": str(tmp_path / "eval_api"),
            "limit": 3,
            "write_artifacts": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario_count"] == 3
    assert "metrics" in payload
    assert "gate" in payload
    assert Path(payload["results_path"]).exists()


def test_eval_run_writes_artifacts_under_the_artifacts_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The dashboard sends only limit and write_artifacts (issue #16).
    monkeypatch.setenv("ECOM_ARTIFACTS_DIR", str(tmp_path))
    client = TestClient(app)
    response = client.post("/v1/evals/run", json={"limit": 1, "write_artifacts": True})

    assert response.status_code == 200
    results_path = Path(response.json()["results_path"])
    assert results_path.is_relative_to(tmp_path)
    run_dirs = list((tmp_path / "eval_api" / "runs").iterdir())
    assert len(run_dirs) == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"output_dir": "../outside"},
        {"output_dir": "/tmp/ecom-resolution-agent-outside"},
        {"dataset_path": "/etc/hosts"},
        {"thresholds_path": "../pyproject.toml"},
    ],
)
def test_eval_run_rejects_paths_outside_allowed_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, overrides: dict[str, str]
) -> None:
    artifacts = tmp_path / "artifacts"
    monkeypatch.setenv("ECOM_ARTIFACTS_DIR", str(artifacts))
    client = TestClient(app)
    response = client.post("/v1/evals/run", json={"limit": 1, **overrides})

    assert response.status_code == 400
    assert not (tmp_path / "outside").exists()
    assert not Path("/tmp/ecom-resolution-agent-outside").exists()


def test_case_run_rejects_run_id_that_leaves_runs_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts = tmp_path / "artifacts"
    monkeypatch.setenv("ECOM_ARTIFACTS_DIR", str(artifacts))
    client = TestClient(app)
    response = client.post(
        "/v1/cases/run",
        json={
            "ticket": {
                "ticket_id": "api_case_002",
                "customer_id": "cus_001",
                "order_id": "ord_001",
                "customer_email": "alice@example.com",
                "issue_type": "delivered_not_received",
                "customer_message": "Delivered but not received",
            },
            "run_id": "../../escaped",
        },
    )

    assert response.status_code == 422
    assert not (tmp_path / "escaped").exists()
