from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ecom_resolution_agent.schemas.agent_outputs import ReportOutput
from ecom_resolution_agent.schemas.audit import AuditEventRecord


class RunArtifactWriter:
    def __init__(self, base_dir: str | Path = "artifacts/runs") -> None:
        self.base_dir = Path(base_dir)

    def run_dir(self, run_id: str) -> Path:
        return self.base_dir / run_id

    def write(
        self,
        *,
        run_id: str,
        run_config: Any,
        audit_events: list[AuditEventRecord | dict[str, Any]],
        decision: Any,
        report_output: ReportOutput | dict[str, Any] | None = None,
        report_markdown: str | None = None,
        evaluation_results: Any | None = None,
    ) -> Path:
        return self.write_bundle(
            run_id=run_id,
            run_config=run_config,
            audit_events=audit_events,
            decision=decision,
            report_output=report_output,
            report_markdown=report_markdown,
            evaluation_results=evaluation_results,
        )

    def write_bundle(
        self,
        *,
        run_id: str,
        run_config: Any,
        audit_events: list[AuditEventRecord | dict[str, Any]],
        decision: Any,
        report_output: ReportOutput | dict[str, Any] | None = None,
        report_markdown: str | None = None,
        evaluation_results: Any | None = None,
    ) -> Path:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(run_dir / "run_config.json", run_config)
        self._write_redacted_audit_jsonl(run_dir / "redacted_audit.jsonl", audit_events)
        self._write_json(run_dir / "decision.json", decision)
        rendered_report_markdown = self._render_report_markdown(
            report_output=report_output,
            report_markdown=report_markdown,
        )
        (run_dir / "report.md").write_text(rendered_report_markdown, encoding="utf-8")

        if evaluation_results is not None:
            self._write_json(run_dir / "evaluation_results.json", evaluation_results)

        return run_dir

    def _write_redacted_audit_jsonl(
        self,
        path: Path,
        audit_events: list[AuditEventRecord | dict[str, Any]],
    ) -> None:
        lines: list[str] = []
        for event in audit_events:
            payload = self._to_jsonable(event)
            lines.append(json.dumps(payload, sort_keys=True))
        path.write_text(("\n".join(lines) + ("\n" if lines else "")), encoding="utf-8")

    def _render_report_markdown(
        self,
        *,
        report_output: ReportOutput | dict[str, Any] | None,
        report_markdown: str | None,
    ) -> str:
        if report_markdown is not None:
            return report_markdown
        if report_output is None:
            return "# Report\n\n_No report content provided._\n"

        report = (
            report_output
            if isinstance(report_output, ReportOutput)
            else ReportOutput.model_validate(report_output)
        )
        refs = "\n".join(f"- `{ref}`" for ref in report.audit_bundle_refs) or "- none"
        return (
            "# Customer Message\n\n"
            f"{report.customer_message_markdown.rstrip()}\n\n"
            "# Internal Summary\n\n"
            f"{report.internal_summary_markdown.rstrip()}\n\n"
            "## Audit Bundle References\n"
            f"{refs}\n"
        )

    def _write_json(self, path: Path, payload: Any) -> None:
        text = json.dumps(self._to_jsonable(payload), indent=2, sort_keys=True) + "\n"
        path.write_text(text, encoding="utf-8")

    def _to_jsonable(self, payload: Any) -> Any:
        if hasattr(payload, "model_dump"):
            return payload.model_dump(mode="json")
        if isinstance(payload, dict):
            return {str(key): self._to_jsonable(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._to_jsonable(item) for item in payload]
        if isinstance(payload, tuple):
            return [self._to_jsonable(item) for item in payload]
        return payload
