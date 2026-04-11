from __future__ import annotations

from typing import Any

from pydantic import Field

from ecom_resolution_agent.schemas.base import StrictModel
from ecom_resolution_agent.tools.schemas.common import KbArticleSummary


class GetPolicyVersionRequest(StrictModel):
    issue_type: str
    country: str | None = None


class GetPolicyVersionResponse(StrictModel):
    policy_version: str


class GetPolicyRulesRequest(StrictModel):
    policy_version: str


class GetPolicyRulesResponse(StrictModel):
    policy_version: str
    rules: dict[str, Any] = Field(default_factory=dict)


class SearchKbArticlesRequest(StrictModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)


class SearchKbArticlesResponse(StrictModel):
    query: str
    results: list[KbArticleSummary] = Field(default_factory=list)
