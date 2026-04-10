.PHONY: install lint typecheck test test_integration format api help

install:
	uv sync --dev

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy src

test:
	uv run pytest tests/unit tests/integration tests/e2e tests/eval

test_integration:
	uv run pytest tests/integration

format:
	uv run ruff format .
	uv run ruff check --fix .

api:
	uv run ecom-resolver api

help:
	uv run python -m ecom_resolution_agent.cli --help
