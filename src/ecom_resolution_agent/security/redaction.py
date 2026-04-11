from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"

_EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\w)")
_PAYMENT_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.\- ]+\s"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b",
    re.IGNORECASE,
)

_SENSITIVE_KEYS = {
    "email",
    "phone",
    "address",
    "street_address",
    "shipping_address",
    "billing_address",
    "payment_identifier",
    "payment_id",
    "card_number",
    "pan",
    "api_key",
    "secret",
    "token",
    "authorization",
}

_TRACKING_KEYS = {"tracking_id", "tracking_number"}


class Redactor:
    """Recursive redaction utility for logs and audit payloads."""

    def redact_text(self, value: str) -> str:
        redacted = _EMAIL_RE.sub(REDACTED, value)
        redacted = _PHONE_RE.sub(REDACTED, redacted)
        redacted = _ADDRESS_RE.sub(REDACTED, redacted)
        redacted = _PAYMENT_RE.sub(REDACTED, redacted)
        return redacted

    def redact_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return self._redact_mapping(value)
        if isinstance(value, list):
            return [self.redact_value(item) for item in value]
        if isinstance(value, tuple):
            return [self.redact_value(item) for item in value]
        if isinstance(value, str):
            return self.redact_text(value)
        return value

    def _redact_mapping(self, mapping: dict[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, raw_value in mapping.items():
            normalized = key.lower()
            if normalized in _SENSITIVE_KEYS or normalized.endswith("_token"):
                redacted[key] = REDACTED
                continue
            if normalized in _TRACKING_KEYS and raw_value is not None:
                redacted[key] = REDACTED
                continue
            redacted[key] = self.redact_value(raw_value)
        return redacted
