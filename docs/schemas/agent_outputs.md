# Agent Output Schemas (Phase 1)

All agent outputs are strict JSON contracts implemented with Pydantic (`extra = forbid`).

## Schemas

- `TriageOutput`
- `PolicyOutput`
- `RiskOutput`
- `ResolutionDecision`
- `QaVerificationResult`
- `ReportOutput`

## Contract Rules

- Unknown fields are rejected.
- Required fields must be present.
- Numeric confidence/risk scores are bounded to `[0, 1]` where applicable.
- String fields are plain JSON strings (no executable content assumptions).

## Example: `TriageOutput`

```json
{
  "issue_type": "delivered_not_received",
  "missing_info_list": [],
  "required_tools_list": ["verify_customer", "get_order", "get_tracking_events"],
  "confidence": 0.94
}
```
