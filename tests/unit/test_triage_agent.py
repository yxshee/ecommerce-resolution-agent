from ecom_resolution_agent.agents import DeterministicTriageAgent


def test_triage_classifies_cancel_and_requests_expected_tools() -> None:
    agent = DeterministicTriageAgent()
    result = agent.classify(
        ticket={"ticket_id": "t1", "customer_id": "cus_001", "order_id": "ord_002"},
        customer_message="Please cancel my order before it ships",
        known_customer_id="cus_001",
        known_order_id="ord_002",
    )

    assert result.issue_type == "cancel_order"
    assert result.missing_info_list == []
    assert "get_fulfillment_status" in result.required_tools_list
    assert result.confidence > 0.8


def test_triage_marks_missing_item_for_return() -> None:
    agent = DeterministicTriageAgent()
    result = agent.classify(
        ticket={"ticket_id": "t2", "customer_id": "cus_001", "order_id": "ord_003"},
        customer_message="I want to return this item",
        known_customer_id="cus_001",
        known_order_id="ord_003",
    )

    assert result.issue_type == "return_initiation"
    assert "item_id" in result.missing_info_list
