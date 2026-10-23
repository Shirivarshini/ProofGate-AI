from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .constants import (
    ALREADY_REFUNDED,
    AMOUNT_EXCEEDS_REMAINING,
    AUTO_CEILING_EXCEEDED,
    CURRENCY,
    CUSTOMER_AUTHORIZATION_FAILED,
    EVALUATION_REFERENCE_TIME,
    EVIDENCE_CONFLICT,
    ELIGIBLE,
    MEDIUM_RISK_CEILING_MINOR,
    ORDER_NOT_DELIVERED,
    POLICY_VIOLATION,
    REFUND_WINDOW_EXPIRED,
    VERIFICATION_UNAVAILABLE,
)


@dataclass(frozen=True)
class PolicyOutcome:
    decision: str
    risk_level: str
    risk_factors: list[str]
    reason_code: str


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _risk(amount_minor: int) -> tuple[str, list[str]]:
    if amount_minor <= MEDIUM_RISK_CEILING_MINOR:
        level = "LOW" if amount_minor <= 100_000 else "MEDIUM"
    else:
        level = "HIGH"
    return level, [f"AMOUNT_{amount_minor}"]


def evaluate_refund(
    arguments: dict[str, Any],
    caller_role: str,
    caller_customer_id: str,
    order: dict[str, Any],
    customer: dict[str, Any],
    policy: dict[str, Any],
) -> PolicyOutcome:
    amount_minor = arguments["amount_minor"]
    risk_level, risk_factors = _risk(amount_minor)

    def blocked(reason_code: str) -> PolicyOutcome:
        return PolicyOutcome("BLOCK", risk_level, risk_factors, reason_code)

    if order.get("customer_id") != arguments["customer_id"]:
        return blocked(CUSTOMER_AUTHORIZATION_FAILED)
    if caller_role == "CUSTOMER" and (
        caller_customer_id != order.get("customer_id")
        or caller_customer_id != arguments["customer_id"]
    ):
        return blocked(CUSTOMER_AUTHORIZATION_FAILED)
    if customer.get("customer_id") != order.get("customer_id"):
        return blocked(CUSTOMER_AUTHORIZATION_FAILED)

    if not isinstance(policy.get("policy_id"), str) or not isinstance(policy.get("version"), str):
        return blocked(VERIFICATION_UNAVAILABLE)
    effective_from = _timestamp(policy.get("effective_from"))
    if effective_from is None or effective_from > EVALUATION_REFERENCE_TIME:
        return blocked(VERIFICATION_UNAVAILABLE)
    refund_window_days = policy.get("refund_window_days")
    automatic_ceiling_minor = policy.get("automatic_ceiling_minor")
    if (
        not isinstance(refund_window_days, int)
        or isinstance(refund_window_days, bool)
        or refund_window_days < 0
        or not isinstance(automatic_ceiling_minor, int)
        or isinstance(automatic_ceiling_minor, bool)
        or automatic_ceiling_minor < 0
    ):
        return blocked(VERIFICATION_UNAVAILABLE)
    if policy.get("currency") != CURRENCY or order.get("currency") != CURRENCY:
        return blocked(POLICY_VIOLATION)
    if arguments.get("currency") != order.get("currency"):
        return blocked(POLICY_VIOLATION)

    delivered_at = _timestamp(order.get("delivered_at"))
    if order.get("status") != "DELIVERED" or delivered_at is None:
        return blocked(ORDER_NOT_DELIVERED)
    if delivered_at > EVALUATION_REFERENCE_TIME:
        return blocked(EVIDENCE_CONFLICT)
    if EVALUATION_REFERENCE_TIME - delivered_at > timedelta(days=refund_window_days):
        return blocked(REFUND_WINDOW_EXPIRED)
    if customer.get("status") != "ACTIVE":
        return blocked(CUSTOMER_AUTHORIZATION_FAILED)

    total_minor = order.get("amount_minor")
    refunded_minor = order.get("refunded_minor")
    if (
        not isinstance(total_minor, int)
        or isinstance(total_minor, bool)
        or total_minor < 0
        or not isinstance(refunded_minor, int)
        or isinstance(refunded_minor, bool)
        or refunded_minor < 0
        or refunded_minor > total_minor
    ):
        return blocked(EVIDENCE_CONFLICT)
    if refunded_minor == total_minor:
        return blocked(ALREADY_REFUNDED)
    remaining_minor = total_minor - refunded_minor
    if amount_minor > remaining_minor:
        return blocked(AMOUNT_EXCEEDS_REMAINING)

    if amount_minor <= automatic_ceiling_minor:
        return PolicyOutcome("APPROVE", risk_level, risk_factors, ELIGIBLE)
    return PolicyOutcome("REVIEW", risk_level, risk_factors, AUTO_CEILING_EXCEEDED)
