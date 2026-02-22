from __future__ import annotations

import re
from dataclasses import dataclass

from ecom_resolution_agent.security.redaction import Redactor


@dataclass(frozen=True)
class PromptInjectionDetection:
    detected: bool
    matched_patterns: list[str]
    evidence_snippets: list[str]


class PromptInjectionDetector:
    def __init__(self, *, redactor: Redactor | None = None) -> None:
        self.redactor = redactor or Redactor()
        self._rules: list[tuple[str, re.Pattern[str]]] = [
            ("ignore_policy", re.compile(r"\bignore\s+(the\s+)?policy\b", re.IGNORECASE)),
            ("refund_anyway", re.compile(r"\brefund\s+anyway\b", re.IGNORECASE)),
            ("reveal_secrets", re.compile(r"\breveal\s+secrets?\b", re.IGNORECASE)),
            ("system_prompt", re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE)),
            ("developer_instructions", re.compile(r"\bdeveloper\s+instructions?\b", re.IGNORECASE)),
            ("tool_schema", re.compile(r"\btool\s+schemas?\b", re.IGNORECASE)),
        ]

    def detect(self, message: str) -> PromptInjectionDetection:
        matched_patterns: list[str] = []
        evidence_snippets: list[str] = []
        for name, pattern in self._rules:
            match = pattern.search(message)
            if match is None:
                continue
            matched_patterns.append(name)
            snippet = message[max(0, match.start() - 24) : min(len(message), match.end() + 24)]
            evidence_snippets.append(self.redactor.redact_text(snippet))

        return PromptInjectionDetection(
            detected=bool(matched_patterns),
            matched_patterns=matched_patterns,
            evidence_snippets=evidence_snippets,
        )
