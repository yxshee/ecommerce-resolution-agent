from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import Field

from ecom_resolution_agent.schemas.base import StrictModel


class PolicyError(Exception):
    """Base policy engine exception."""


class PolicyNotFoundError(PolicyError):
    """Raised when a policy version directory does not exist."""


class PolicyValidationError(PolicyError):
    """Raised when metadata or rules files are malformed."""


class PolicyChecksumError(PolicyError):
    """Raised when metadata checksum does not match rules file content."""


class PolicyMetadata(StrictModel):
    version: str
    status: str
    effective_date: str
    rules_sha256: str


class PolicyVariant(StrictModel):
    name: str
    when: dict[str, Any] = Field(default_factory=dict)
    allowed_actions: list[str]
    constraints: dict[str, Any] = Field(default_factory=dict)
    required_evidence: list[str] = Field(default_factory=list)
    approval_required: bool = False
    approval_overrides: dict[str, Any] = Field(default_factory=dict)
    on_missing_evidence: str = "escalate_human"


class PolicyIssueRule(StrictModel):
    default: PolicyVariant
    variants: list[PolicyVariant] = Field(default_factory=list)


class PolicyRulesDocument(StrictModel):
    version: str
    issue_rules: dict[str, PolicyIssueRule]


@dataclass(frozen=True)
class LoadedPolicyBundle:
    metadata: PolicyMetadata
    rules: PolicyRulesDocument
    rules_path: Path
    metadata_path: Path


class PolicyLoader:
    def __init__(self, root: str | Path = "policies/versions") -> None:
        self.root = Path(root)

    def load(self, version: str) -> LoadedPolicyBundle:
        version_dir = self.root / version
        if not version_dir.exists():
            raise PolicyNotFoundError(f"Policy version not found: {version}")

        metadata_path = version_dir / "metadata.json"
        rules_path = version_dir / "rules.json"
        try:
            metadata_payload = json.loads(metadata_path.read_text())
            rules_payload = json.loads(rules_path.read_text())
        except FileNotFoundError as exc:
            raise PolicyNotFoundError(f"Missing policy file: {exc.filename}") from exc
        except json.JSONDecodeError as exc:
            raise PolicyValidationError(f"Malformed JSON in policy files: {exc}") from exc

        try:
            metadata = PolicyMetadata.model_validate(metadata_payload)
            rules = PolicyRulesDocument.model_validate(rules_payload)
        except Exception as exc:  # noqa: BLE001 - surface as policy validation error
            raise PolicyValidationError(str(exc)) from exc

        self._validate_checksum(metadata, rules_path)

        if metadata.version != rules.version or metadata.version != version:
            raise PolicyValidationError(
                "Policy version mismatch between directory, metadata, and rules"
            )

        return LoadedPolicyBundle(
            metadata=metadata,
            rules=rules,
            rules_path=rules_path,
            metadata_path=metadata_path,
        )

    @staticmethod
    def _validate_checksum(metadata: PolicyMetadata, rules_path: Path) -> None:
        digest = hashlib.sha256(rules_path.read_bytes()).hexdigest()
        if digest != metadata.rules_sha256:
            raise PolicyChecksumError(
                "rules_sha256 mismatch for "
                f"{metadata.version}: expected {metadata.rules_sha256}, got {digest}"
            )
