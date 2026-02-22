from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ecom_resolution_agent.policy import (
    PolicyChecksumError,
    PolicyLoader,
    PolicyNotFoundError,
    PolicyService,
    PolicyValidationError,
)


def test_policy_loader_loads_v1_and_verifies_checksum() -> None:
    loader = PolicyLoader()
    bundle = loader.load("v1_0_0")

    assert bundle.metadata.version == "v1_0_0"
    assert bundle.rules.version == "v1_0_0"
    expected = hashlib.sha256(bundle.rules_path.read_bytes()).hexdigest()
    assert bundle.metadata.rules_sha256 == expected


def test_cancel_order_pre_shipment_allows_cancel() -> None:
    service = PolicyService()
    result = service.evaluate(
        issue_type="cancel_order",
        policy_version="v1_0_0",
        facts={
            "fulfillment_status": "pending",
            "available_evidence": ["order", "fulfillment_status"],
        },
    )

    assert "cancel_order" in result.allowed_actions
    assert result.approval_required is False


def test_cancel_order_shipped_disallows_cancel() -> None:
    service = PolicyService()
    result = service.evaluate(
        issue_type="cancel_order",
        policy_version="v1_0_0",
        facts={
            "fulfillment_status": "shipped",
            "available_evidence": ["order", "fulfillment_status"],
        },
    )

    assert result.allowed_actions == ["escalate_human"]


def test_return_initiation_missing_evidence_escalates() -> None:
    service = PolicyService()
    result = service.evaluate(
        issue_type="return_initiation",
        policy_version="v1_0_0",
        facts={"available_evidence": ["order", "order_items"]},
    )

    assert result.allowed_actions == ["escalate_human"]
    assert result.constraints["missing_evidence"] == ["item_id"]


def test_delivered_not_received_high_value_requires_approval() -> None:
    service = PolicyService()
    result = service.evaluate(
        issue_type="delivered_not_received",
        policy_version="v1_0_0",
        facts={
            "order_total_cents": 80000,
            "delivery_proof_available": True,
            "available_evidence": ["tracking_events", "delivery_proof"],
        },
    )

    assert "refund_full" in result.allowed_actions
    assert result.approval_required is True


def test_unknown_version_raises_not_found() -> None:
    loader = PolicyLoader()
    with pytest.raises(PolicyNotFoundError):
        loader.load("v9_9_9")


def test_malformed_policy_file_raises_validation(tmp_path: Path) -> None:
    version_dir = tmp_path / "v_bad"
    version_dir.mkdir(parents=True)
    (version_dir / "metadata.json").write_text(
        json.dumps(
            {
                "version": "v_bad",
                "status": "active",
                "effective_date": "2026-02-22",
                "rules_sha256": "deadbeef",
            }
        )
    )
    (version_dir / "rules.json").write_text(json.dumps({"version": "v_bad"}))

    loader = PolicyLoader(tmp_path)
    with pytest.raises((PolicyValidationError, PolicyChecksumError)):
        loader.load("v_bad")
