from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft202012Validator, FormatChecker

from backend.main import app
from backend.scenario_runner import run_scenarios
from backend.verification import InvalidActionError, RefundVerifier

ROOT = Path(__file__).resolve().parents[1]


def _action(
    *,
    action_id: str = "act_TEST",
    order_id: str = "ord_001",
    customer_id: str = "cus_001",
    actor_id: str | None = None,
    amount_minor: int = 129_900,
) -> dict:
    return {
        "action_id": action_id,
        "schema_version": "1.0",
        "tool_name": "refund.create",
        "arguments": {
            "order_id": order_id,
            "customer_id": customer_id,
            "amount_minor": amount_minor,
            "currency": "INR",
            "reason": "Item damaged",
        },
        "actor_context": {
            "actor_id": actor_id or customer_id,
            "actor_type": "CUSTOMER",
            "request_id": "req_TEST",
        },
    }


def test_all_scenarios_match_expected_results() -> None:
    report = run_scenarios()
    assert report["mode"] == "DETERMINISTIC_FIXTURE_EVALUATION"
    assert report["scenario_count"] == 20
    assert report["failed"] == 0


@pytest.mark.parametrize(
    ("action", "expected_decision", "expected_reason"),
    [
        (_action(), "APPROVE", "ELIGIBLE"),
        (
            _action(order_id="ord_009", customer_id="cus_001"),
            "BLOCK",
            "CUSTOMER_AUTHORIZATION_FAILED",
        ),
        (
            _action(order_id="ord_003", customer_id="cus_003"),
            "BLOCK",
            "REFUND_WINDOW_EXPIRED",
        ),
        (
            _action(order_id="ord_001", amount_minor=129_901),
            "BLOCK",
            "AMOUNT_EXCEEDS_REMAINING",
        ),
    ],
)
def test_refund_verification(
    action: dict, expected_decision: str, expected_reason: str
) -> None:
    result = RefundVerifier().verify(action)
    assert result["decision"] == expected_decision
    assert expected_reason in result["reason_codes"]


def test_high_value_is_review_not_execution() -> None:
    result = RefundVerifier().verify(
        _action(order_id="ord_002", customer_id="cus_002", amount_minor=250_000)
    )
    assert result["decision"] == "REVIEW"
    assert result["execution_status"] == "PENDING_REVIEW"


def test_invalid_action_fails_with_schema_errors() -> None:
    action = _action()
    action["arguments"]["amount_minor"] = True
    with pytest.raises(InvalidActionError) as error:
        RefundVerifier().verify(action)
    assert error.value.code == "INVALID_ACTION_SCHEMA"


def test_approved_output_conforms_to_shared_schema() -> None:
    result = RefundVerifier().verify(_action())
    schema_path = ROOT / "contracts" / "verification.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)


def test_verification_emits_redacted_audit_events(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("INFO", logger="backend.verification"):
        RefundVerifier().verify(_action())

    events = [json.loads(record.message) for record in caplog.records]
    completed = next(
        event for event in events if event["event_type"] == "VERIFICATION_COMPLETED"
    )
    assert completed["payload"] == {
        "decision": "APPROVE",
        "risk_level": "MEDIUM",
        "reason_codes": ["ELIGIBLE"],
        "execution_status": "NOT_STARTED",
        "evidence_count": 3,
        "policy_version": "1.0",
    }
    assert "email" not in completed["payload"]
    audit_schema = json.loads(
        (ROOT / "contracts" / "audit.schema.json").read_text(encoding="utf-8")
    )
    audit_validator = Draft202012Validator(
        audit_schema, format_checker=FormatChecker()
    )
    for event in events:
        audit_validator.validate(event)


def test_health_endpoint_matches_openapi_contract() -> None:
    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.get("/health")

    response = asyncio.run(request_health())
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_prompt_injection_text_does_not_change_trusted_evidence() -> None:
    scenarios = json.loads(
        (ROOT / "data" / "test_scenarios.json").read_text(encoding="utf-8")
    )
    scenario = next(item for item in scenarios if item["scenario_id"] == "scn_019")
    action = _action(
        action_id="act_SCN_019",
        order_id=scenario["order_id"],
        customer_id=scenario["customer_id"],
        amount_minor=70_000,
    )
    action["arguments"]["reason"] = scenario["request"]
    result = RefundVerifier().verify(action)
    assert result["decision"] == "APPROVE"
    assert result["reason_codes"] == ["ELIGIBLE"]
