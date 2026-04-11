# Redaction Utility (Phase 1)

The redaction utility provides recursive redaction for structured logs and audit payloads.

## Redacted by pattern

- Emails
- Phone numbers
- Street-address-like strings (best effort)
- Payment-card-like digit sequences (best effort)

## Redacted by key name

Sensitive keys are redacted regardless of value content, including:

- `email`
- `phone`
- `address` / `shipping_address` / `billing_address`
- `payment_identifier`
- `card_number`
- `token`, `*_token`, `authorization`, `api_key`, `secret`
- `tracking_id`, `tracking_number`

## Usage

Use `Redactor.redact_value()` before writing any tool input/output to logs or audit tables.
