from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class IdempotencyKeyInput:
    order_id: str
    action_type: str
    item_id: str | None = None
    amount_cents: int | None = None
    currency: str | None = None
    policy_version: str | None = None


def build_idempotency_key(payload: IdempotencyKeyInput) -> str:
    canonical = {
        "order_id": payload.order_id,
        "action_type": payload.action_type,
        "item_id": payload.item_id,
        "amount_cents": payload.amount_cents,
        "currency": payload.currency,
        "policy_version": payload.policy_version,
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"idem_{digest[:16]}"
