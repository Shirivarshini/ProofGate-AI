"""Run deterministic verification against every checked-in test scenario."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from backend.verification import (
    DATA_DIR,
    FixtureDataError,
    RefundVerifier,
    _read_json,
    scenario_amount_minor,
)

logger = logging.getLogger(__name__)


def run_scenarios() -> dict[str, Any]:
    scenarios = _read_json(DATA_DIR / "test_scenarios.json")
    if not isinstance(scenarios, list):
        raise FixtureDataError("test_scenarios.json must contain a JSON array.")

    verifier = RefundVerifier()
    order_records = _read_json(DATA_DIR / "orders.json")
    orders_by_id = {order["order_id"]: order for order in order_records}
    results: list[dict[str, Any]] = []

    for scenario in scenarios:
        order = orders_by_id.get(scenario["order_id"])
        if order is None:
            amount_minor = 1
        else:
            remaining = order["amount_minor"] - order["refunded_minor"]
            amount_minor = max(
                1, scenario_amount_minor(scenario["request"], remaining)
            )
        action = {
            "action_id": f"act_{scenario['scenario_id'][4:]}",
            "schema_version": "1.0",
            "tool_name": "refund.create",
            "arguments": {
                "order_id": scenario["order_id"],
                "customer_id": scenario["customer_id"],
                "amount_minor": amount_minor,
                "currency": "INR",
                "reason": scenario["request"][:500],
            },
            "actor_context": {
                "actor_id": scenario["customer_id"],
                "actor_type": "CUSTOMER",
                "request_id": scenario["scenario_id"],
            },
        }
        actual = verifier.verify(action)
        actual_fields = {
            "decision": actual["decision"],
            "execution_status": actual["execution_status"],
            "reason_codes": actual["reason_codes"],
        }
        expected_fields = {
            "decision": scenario["expected_decision"],
            "execution_status": scenario["expected_execution_status"],
            "reason_codes": scenario["expected_reason_codes"],
        }
        results.append(
            {
                "scenario_id": scenario["scenario_id"],
                "passed": actual_fields == expected_fields,
                "expected": expected_fields,
                "actual": actual_fields,
                "risk_level": actual["risk_assessment"]["level"],
            }
        )

    return {
        "mode": "DETERMINISTIC_FIXTURE_EVALUATION",
        "scenario_count": len(results),
        "passed": sum(result["passed"] for result in results),
        "failed": sum(not result["passed"] for result in results),
        "results": results,
    }


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    try:
        report = run_scenarios()
    except (FixtureDataError, KeyError, TypeError, ValueError):
        logger.exception("Scenario evaluation failed.")
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
