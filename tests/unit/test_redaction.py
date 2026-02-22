from ecom_resolution_agent.security.redaction import REDACTED, Redactor


def test_redact_text_patterns() -> None:
    redactor = Redactor()
    text = (
        "Contact me at user@example.com or (415) 555-1212. "
        "Ship to 123 Main Street. Card 4111 1111 1111 1111."
    )
    result = redactor.redact_text(text)

    assert "user@example.com" not in result
    assert "555-1212" not in result
    assert "123 Main Street" not in result
    assert "4111 1111 1111 1111" not in result
    assert result.count(REDACTED) >= 4


def test_redact_nested_values_and_sensitive_keys() -> None:
    redactor = Redactor()
    payload = {
        "email": "person@example.com",
        "customer": {
            "phone": "+1 212 555 0199",
            "shipping_address": "500 Market Street",
            "notes": "Tracking number 1Z999AA10123456784",
        },
        "payment_identifier": "pi_12345",
        "tracking_id": "1Z999AA10123456784",
        "safe_value": "order_status",
    }

    redacted = redactor.redact_value(payload)

    assert redacted["email"] == REDACTED
    assert redacted["customer"]["phone"] == REDACTED
    assert redacted["customer"]["shipping_address"] == REDACTED
    assert redacted["payment_identifier"] == REDACTED
    assert redacted["tracking_id"] == REDACTED
    assert redacted["safe_value"] == "order_status"
