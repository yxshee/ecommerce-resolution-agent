# Tool Envelope Schemas (Phase 1)

Tool calls are wrapped in strict request/result envelopes to improve auditability and deterministic validation.

## Schemas

- `ToolCallContext`
- `ToolCallRequest[T]`
- `ToolCallResult[T]`
- `ToolError`

## Validation Rules

- `ToolCallResult.ok = true` requires `error = null`
- `ToolCallResult.ok = false` requires a populated `error`
- `latency_ms` must be non-negative
- Unknown fields are rejected (`extra = forbid`)

## Example Result

```json
{
  "tool_name": "get_order",
  "ok": true,
  "data": {"order_id": "ord_123"},
  "error": null,
  "external_reference": null,
  "latency_ms": 42,
  "simulated": true
}
```
