import json
import re
import uuid
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

from .constants import (
    ACTION_SCHEMA_INVALID,
    CUSTOMER_AUTHORIZATION_FAILED,
    EVALUATION_REFERENCE_TIME,
    EVIDENCE_MISSING,
    ORDER_NOT_FOUND,
    VERIFICATION_UNAVAILABLE,
)
from .evidence import EvidenceStore, EvidenceStoreError
from .policy import PolicyOutcome, evaluate_refund

_ACTION_ID_PATTERN = re.compile(r"^act_[A-Z0-9_]+$")
_CUSTOMER_ID_PATTERN = re.compile(r"^cus_[A-Z0-9_]+$")


@dataclass(frozen=True)
class CallerContext:
    role: str
    customer_id: str


@lru_cache(maxsize=1)
def _action_validator() -> Draft202012Validator:
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "action.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@lru_cache(maxsize=1)
def _verification_validator() -> Draft202012Validator:
    schema_path = Path(__file__).resolve().parents[2] / "contracts" / "verification.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _verified_at() -> str:
    return EVALUATION_REFERENCE_TIME.isoformat().replace("+00:00", "Z")


def _risk_for_amount(amount: Any) -> tuple[str, list[str]]:
    if type(amount) is not int or amount < 1:
        return "LOW", ["AMOUNT_UNKNOWN"]
    if amount <= 100_000:
        return "LOW", [f"AMOUNT_{amount}"]
    if amount <= 200_000:
        return "MEDIUM", [f"AMOUNT_{amount}"]
    return "HIGH", [f"AMOUNT_{amount}"]


def _result(
    action_id: str,
    decision: str,
    risk_level: str,
    risk_factors: list[str],
    reason_code: str,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = {
        "verification_id": f"ver_{uuid.uuid4().hex.upper()}",
        "action_id": action_id,
        "decision": decision,
        "risk_assessment": {"level": risk_level, "factors": risk_factors},
        "reason_codes": [reason_code],
        "evidence": evidence or [],
        "execution_status": "PENDING_REVIEW" if decision == "REVIEW" else (
            "NOT_STARTED" if decision == "APPROVE" else "NOT_EXECUTED"
        ),
        "verified_at": _verified_at(),
    }
    _verification_validator().validate(result)
    return result


def _action_id(action: Any) -> str:
    candidate = action.get("action_id") if isinstance(action, dict) else None
    return candidate if isinstance(candidate, str) and _ACTION_ID_PATTERN.fullmatch(candidate) else "act_INVALID_ACTION"


def _valid_caller(caller: Any) -> bool:
    if not isinstance(caller, CallerContext):
        return False
    if not isinstance(caller.role, str) or caller.role not in {"CUSTOMER", "SUPPORT_AGENT"}:
        return False
    if not isinstance(caller.customer_id, str) or not caller.customer_id:
        return False
    return caller.role != "CUSTOMER" or bool(_CUSTOMER_ID_PATTERN.fullmatch(caller.customer_id))


def verify(
    action: Any,
    caller: CallerContext,
    evidence_store: EvidenceStore | None = None,
) -> dict[str, Any]:
    action_id = _action_id(action)
    try:
        _action_validator().validate(action)
    except ValidationError:
        risk_level, factors = _risk_for_amount(
            action.get("arguments", {}).get("amount_minor")
            if isinstance(action, dict) and isinstance(action.get("arguments"), dict)
            else None
        )
        return _result(action_id, "BLOCK", risk_level, factors, ACTION_SCHEMA_INVALID)
    except (OSError, json.JSONDecodeError, SchemaError):
        risk_level, factors = _risk_for_amount(
            action.get("arguments", {}).get("amount_minor")
            if isinstance(action, dict) and isinstance(action.get("arguments"), dict)
            else None
        )
        return _result(action_id, "BLOCK", risk_level, factors, VERIFICATION_UNAVAILABLE)

    if not _valid_caller(caller):
        risk_level, factors = _risk_for_amount(action["arguments"]["amount_minor"])
        return _result(action_id, "BLOCK", risk_level, factors, CUSTOMER_AUTHORIZATION_FAILED)

    try:
        store = evidence_store or EvidenceStore.from_directory()
    except EvidenceStoreError:
        risk_level, factors = _risk_for_amount(action["arguments"]["amount_minor"])
        return _result(action_id, "BLOCK", risk_level, factors, VERIFICATION_UNAVAILABLE)
    except (OSError, json.JSONDecodeError, SchemaError):
        risk_level, factors = _risk_for_amount(action["arguments"]["amount_minor"])
        return _result(action_id, "BLOCK", risk_level, factors, VERIFICATION_UNAVAILABLE)

    arguments = action["arguments"]
    order = store.get_order(arguments["order_id"])
    if order is None:
        risk_level, factors = _risk_for_amount(arguments["amount_minor"])
        return _result(action_id, "BLOCK", risk_level, factors, ORDER_NOT_FOUND)

    order_customer_id = order.get("customer_id")
    customer = store.get_customer(order_customer_id) if isinstance(order_customer_id, str) else None
    requested_customer = store.get_customer(arguments["customer_id"])
    policy = store.get_policy()
    if customer is None or requested_customer is None:
        risk_level, factors = _risk_for_amount(arguments["amount_minor"])
        return _result(action_id, "BLOCK", risk_level, factors, EVIDENCE_MISSING)
    if policy is None:
        risk_level, factors = _risk_for_amount(arguments["amount_minor"])
        return _result(action_id, "BLOCK", risk_level, factors, VERIFICATION_UNAVAILABLE)

    outcome: PolicyOutcome = evaluate_refund(
        arguments,
        caller.role,
        caller.customer_id,
        order,
        customer,
        policy,
    )
    evidence = store.snapshots(order, customer, policy, _verified_at())
    return _result(
        action_id,
        outcome.decision,
        outcome.risk_level,
        outcome.risk_factors,
        outcome.reason_code,
        evidence,
    )


def to_api_response(verification: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_id": verification["action_id"],
        "verification_decision": verification["decision"],
        "risk_level": verification["risk_assessment"]["level"],
        "execution_status": verification["execution_status"],
        "reason_codes": list(verification["reason_codes"]),
        "evidence": list(verification["evidence"]),
    }
