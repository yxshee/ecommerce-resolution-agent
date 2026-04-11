# Tool Permissions (Phase 2)

Least-privilege access is enforced in `ToolExecutor` using a static capability matrix by agent role.

## Rules

- Unknown agents have no tool access by default.
- Action tools are denied unless the actor is permitted.
- Real action execution is blocked unless explicitly enabled in executor config and simulation mode is off.
- All tool inputs/outputs are redacted before audit logging.

## Capability Matrix (Current)

### `triage`

Allowed:

- `verify_customer`
- `get_customer_profile`
- `get_order`
- `get_order_items`
- `get_fulfillment_status`
- `get_tracking_events`
- `get_delivery_proof`
- `get_policy_version`
- `get_policy_rules`
- `search_kb_articles`

Denied examples:

- `issue_refund`
- `create_return`
- `reserve_stock`

### `policy`

Allowed:

- `get_policy_version`
- `get_policy_rules`
- `search_kb_articles`

### `risk`

Allowed (read-only evidence/facts):

- `get_customer_profile`
- `get_order`
- `get_order_items`
- `get_fulfillment_status`
- `get_tracking_events`
- `get_delivery_proof`

### `actions`

Allowed (actions + related checks):

- `create_return`
- `create_label`
- `schedule_pickup`
- `issue_refund`
- `get_refund_status`
- `check_stock`
- `reserve_stock`
- `update_ticket`
- `add_internal_note`

### `qa`

Allowed:

- Read-only order/shipping/customer facts
- Knowledge base lookups
- `get_refund_status`

### `report`

Allowed:

- `update_ticket`
- `add_internal_note`
- `search_kb_articles`

### `system`

- `*` (wildcard, internal maintenance/testing only)
