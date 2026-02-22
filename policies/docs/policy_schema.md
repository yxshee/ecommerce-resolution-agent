# Policy Schema (Phase 3)

Policies are versioned JSON documents stored under `policies/versions/<version>/`.

## Files per version

- `metadata.json`: metadata + checksum
- `rules.json`: deterministic rules document

## `metadata.json`

Required fields:

- `version`
- `status`
- `effective_date`
- `rules_sha256`

## `rules.json` top-level

- `version`
- `issue_rules` (object keyed by issue type)

## Issue rule shape

Each issue rule contains:

- `default` (`PolicyVariant`)
- `variants` (ordered list of `PolicyVariant`; first matching variant wins)

## `PolicyVariant` fields

- `name`
- `when` (optional match conditions)
  - `fact_equals`
  - `fact_in`
  - `fact_gte`
- `allowed_actions`
- `constraints`
- `required_evidence`
- `approval_required`
- `approval_overrides`
- `on_missing_evidence` (`escalate_human` or `defer`)

## Evaluation behavior

- Unknown issue type -> `escalate_human` with approval required
- Missing required evidence -> escalates (or defers if configured)
- Approval can be forced by static `approval_required` or dynamic `approval_overrides`
