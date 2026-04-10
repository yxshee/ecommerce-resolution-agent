from fastapi.testclient import TestClient
from typer.testing import CliRunner

from ecom_resolution_agent.api.app import app as fastapi_app
from ecom_resolution_agent.cli import app as cli_app

runner = CliRunner()


def test_healthz_endpoint_returns_ok() -> None:
    client = TestClient(fastapi_app)
    response = client.get("/healthz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["simulation_mode"] is True


def test_cli_help_smoke() -> None:
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0
    assert "Ecommerce Resolution Agent CLI" in result.stdout
    assert "run-case" in result.stdout
    assert "api" in result.stdout
