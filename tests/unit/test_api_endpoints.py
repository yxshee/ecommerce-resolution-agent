from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ecom_resolution_agent.api.app import app


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


def test_eval_run_endpoint_supports_limited_run(tmp_path: Path) -> None:
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
