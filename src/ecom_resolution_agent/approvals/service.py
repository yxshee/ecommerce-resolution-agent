from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol

from ecom_resolution_agent.schemas.actions import ApprovalTokenClaims

try:
    from redis import Redis
except Exception:  # noqa: BLE001
    Redis = object  # type: ignore[assignment,misc]


class ApprovalTokenStoreProtocol(Protocol):
    def issue(self, token: str, claims: ApprovalTokenClaims, ttl_seconds: int) -> None: ...
    def consume(self, token: str) -> ApprovalTokenClaims | None: ...


@dataclass
class InMemoryApprovalTokenStore(ApprovalTokenStoreProtocol):
    _entries: dict[str, tuple[ApprovalTokenClaims, datetime]] = field(default_factory=dict)

    def issue(self, token: str, claims: ApprovalTokenClaims, ttl_seconds: int) -> None:
        self._entries[token] = (claims, datetime.now(UTC) + timedelta(seconds=ttl_seconds))

    def consume(self, token: str) -> ApprovalTokenClaims | None:
        entry = self._entries.pop(token, None)
        if entry is None:
            return None
        claims, expires_at = entry
        if datetime.now(UTC) >= expires_at:
            return None
        return claims


class RedisApprovalTokenStore(ApprovalTokenStoreProtocol):
    def __init__(self, client: Redis, prefix: str = "approval_token:") -> None:
        self.client = client
        self.prefix = prefix

    def issue(self, token: str, claims: ApprovalTokenClaims, ttl_seconds: int) -> None:
        key = f"{self.prefix}{token}"
        self.client.set(key, claims.model_dump_json(), ex=ttl_seconds)

    def consume(self, token: str) -> ApprovalTokenClaims | None:
        key = f"{self.prefix}{token}"
        # Prefer GETDEL for one-time use semantics when supported.
        payload = self.client.execute_command("GETDEL", key)
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ApprovalTokenClaims.model_validate_json(payload)


@dataclass(frozen=True)
class ApprovalTaskRecord:
    approval_task_id: str
    run_id: str
    action_type: str
    status: str
    requested_reason: str
    ticket_id: str | None = None
    token_id: str | None = None


@dataclass(frozen=True)
class ApprovalRequestResult:
    task: ApprovalTaskRecord
    token: str
    claims: ApprovalTokenClaims


class ApprovalService:
    def __init__(
        self,
        token_store: ApprovalTokenStoreProtocol | None = None,
    ) -> None:
        self.token_store = token_store or InMemoryApprovalTokenStore()
        self._tasks: dict[str, ApprovalTaskRecord] = {}

    def request_approval(
        self,
        *,
        run_id: str,
        action_type: str,
        order_id: str,
        requested_reason: str,
        ticket_id: str | None = None,
        max_amount_cents: int | None = None,
        ttl_seconds: int = 900,
    ) -> ApprovalRequestResult:
        token_id = f"apt_{uuid.uuid4().hex[:16]}"
        token = f"approval_{uuid.uuid4().hex}"
        claims = ApprovalTokenClaims(
            token_id=token_id,
            run_id=run_id,
            action_type=action_type,
            order_id=order_id,
            max_amount_cents=max_amount_cents,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )
        self.token_store.issue(token, claims, ttl_seconds)

        task = ApprovalTaskRecord(
            approval_task_id=f"appr_{uuid.uuid4().hex[:16]}",
            run_id=run_id,
            ticket_id=ticket_id,
            action_type=action_type,
            status="PENDING",
            requested_reason=requested_reason,
            token_id=token_id,
        )
        self._tasks[task.approval_task_id] = task
        return ApprovalRequestResult(task=task, token=token, claims=claims)

    def consume_approval_token(self, token: str) -> ApprovalTokenClaims | None:
        return self.token_store.consume(token)

    def get_task(self, approval_task_id: str) -> ApprovalTaskRecord | None:
        return self._tasks.get(approval_task_id)
