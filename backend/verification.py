"""Deterministic refund verification against trusted local fixture records."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT / "contracts"
DATA_DIR = ROOT / "data"


class VerificationError(Exception):
    """Base exception for explicit verification failures."""

    code = "VERIFICATION_UNAVAILABLE"


class InvalidActionError(VerificationError):
    code = "INVALID_ACTION_SCHEMA"

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("Action does not conform to the EAC schema.")


class FixtureDataError(VerificationError):
    code = "VERIFICATION_UNAVAILABLE"


def _read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("Unable to load ProofGate fixture file: %s", path)
        raise FixtureDataError(f"Unable to load required fixture: {path.name}") from exc


def _schema_validator(schema_path: Path) -> Draft202012Validator:
    schema = _read_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        logger.exception("Invalid JSON Schema: %s", schema_path)
        raise FixtureDataError(f"Invalid contract schema: {schema_path.name}") from exc
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _validate_action(action: Any, validator: Draft202012Validator) -> dict[str, Any]:
    errors = sorted(
        validator.iter_errors(action),
        key=lambda error: (list(map(str, error.absolute_path)), error.message),
    )
    if errors:
        details = [
            f"{'.'.join(map(str, error.absolute_path)) or '$'}: {error.message}"
            for error in errors
        ]
        logger.warning("Action rejected by EAC schema: %s", "; ".join(details))
        raise InvalidActionError(details)
    return action


def _record_digest(record: dict[str, Any]) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _evidence(
    source_type: str,
    source_id: str,
    record: dict[str, Any],
    retrieved_at: str,
) -> dict[str, Any]:
    version: str | int = record.get("version", "1.0")
    return {
        "evidence_id": f"ev_{source_type}_{source_id}",
        "source_type": source_type,
        "source_id": source_id,
        "version": version,
        "retrieved_at": retrieved_at,
        "digest": _record_digest(record),
    }


def _log_audit_event(action_id: str, event_type: str, payload: dict[str, Any]) -> None:
    event = {
        "audit_id": f"aud_{uuid.uuid4().hex[:16].upper()}",
        "action_id": action_id,
        "event_type": event_type,
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "payload": payload,
    }
    logger.info("%s", json.dumps(event, sort_keys=True, separators=(",", ":")))


def _result(
    action_id: str,
    decision: str,
    risk_level: str,
    factors: list[str],
    reason_codes: list[str],
    evidence: list[dict[str, Any]],
    verified_at: str,
) -> dict[str, Any]:
    if decision == "REVIEW":
        execution_status = "PENDING_REVIEW"
    elif decision == "BLOCK":
        execution_status = "NOT_EXECUTED"
    else:
        execution_status = "NOT_STARTED"
    return {
        "verification_id": f"ver_{uuid.uuid4().hex[:16].upper()}",
        "action_id": action_id,
        "decision": decision,
        "risk_assessment": {"level": risk_level, "factors": factors},
        "reason_codes": reason_codes,
        "evidence": evidence,
        "execution_status": execution_status,
        "verified_at": verified_at,
    }


class RefundVerifier:
    """Evaluate a refund action using independently loaded local trusted data."""

    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        contracts_dir: Path = CONTRACTS_DIR,
    ) -> None:
        self.data_dir = data_dir
        self.contracts_dir = contracts_dir

    def verify(self, action: Any) -> dict[str, Any]:
        action_validator = _schema_validator(
            self.contracts_dir / "action.schema.json"
        )
        verified_action = _validate_action(action, action_validator)
        _log_audit_event(
            verified_action["action_id"],
            "ACTION_RECEIVED",
            {"tool_name": verified_action["tool_name"]},
        )

        verification_validator = _schema_validator(
            self.contracts_dir / "verification.schema.json"
        )
        customers = self._index(self.data_dir / "customers.json", "customer_id")
        orders = self._index(self.data_dir / "orders.json", "order_id")
        policy = self._load_policy()
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        args = verified_action["arguments"]
        actor = verified_action["actor_context"]
        order = orders.get(args["order_id"])
        customer = customers.get(args["customer_id"])
        evidence = [
            _evidence("POLICY", policy["policy_id"], policy, now),
        ]
        if order is not None:
            evidence.append(_evidence("ORDER", args["order_id"], order, now))
        if customer is not None:
            evidence.append(_evidence("CUSTOMER", args["customer_id"], customer, now))

        action_id = verified_action["action_id"]
        decision: str
        reason: str
        risk = "LOW"
        factors: list[str] = []

        if order is None:
            decision, reason = "BLOCK", "ORDER_NOT_FOUND"
        elif customer is None:
            decision, reason = "BLOCK", "EVIDENCE_MISSING"
        elif (
            customer.get("status") != "ACTIVE"
            or order.get("customer_id") != args["customer_id"]
            or actor.get("actor_type") != "CUSTOMER"
            or actor.get("actor_id") != args["customer_id"]
        ):
            decision, reason = "BLOCK", "CUSTOMER_AUTHORIZATION_FAILED"
        elif order.get("currency") != policy.get("currency") or args.get(
            "currency"
        ) != policy.get("currency"):
            decision, reason = "BLOCK", "POLICY_VIOLATION"
        elif order.get("status") != policy.get("required_order_status"):
            decision, reason = "BLOCK", "ORDER_NOT_DELIVERED"
        elif not isinstance(order.get("delivered_at"), str):
            decision, reason = "BLOCK", "EVIDENCE_CONFLICT"
        elif not self._within_refund_window(order, policy):
            decision, reason = "BLOCK", "REFUND_WINDOW_EXPIRED"
        elif (
            order.get("refunded_minor", 0) < 0
            or order.get("amount_minor", 0) < 0
            or order.get("refunded_minor", 0) > order.get("amount_minor", 0)
        ):
            decision, reason = "BLOCK", "EVIDENCE_CONFLICT"
        elif order.get("refunded_minor", 0) == order.get("amount_minor", 0):
            decision, reason = "BLOCK", "ALREADY_REFUNDED"
        elif args["amount_minor"] > (
            order["amount_minor"] - order["refunded_minor"]
        ):
            decision, reason = "BLOCK", "AMOUNT_EXCEEDS_REMAINING"
        else:
            decision, reason, risk, factors = self._assess_eligible_action(
                args["amount_minor"], policy
            )

        result = _result(
            action_id=action_id,
            decision=decision,
            risk_level=risk,
            factors=factors,
            reason_codes=[reason],
            evidence=evidence,
            verified_at=now,
        )
        errors = list(verification_validator.iter_errors(result))
        if errors:
            for error in errors:
                logger.error("Verifier produced contract-invalid output: %s", error)
            raise FixtureDataError(
                "Verification output does not conform to the shared result schema."
            )
        _log_audit_event(
            action_id,
            "VERIFICATION_COMPLETED",
            {
                "decision": result["decision"],
                "risk_level": result["risk_assessment"]["level"],
                "reason_codes": result["reason_codes"],
                "execution_status": result["execution_status"],
                "evidence_count": len(result["evidence"]),
                "policy_version": policy["version"],
            },
        )
        return result

    def _index(self, path: Path, key: str) -> dict[str, dict[str, Any]]:
        records = _read_json(path)
        if not isinstance(records, list):
            raise FixtureDataError(f"{path.name} must contain a JSON array.")
        indexed: dict[str, dict[str, Any]] = {}
        for record in records:
            if not isinstance(record, dict) or not isinstance(record.get(key), str):
                raise FixtureDataError(f"{path.name} contains an invalid record.")
            required_fields = (
                {"customer_id", "name", "email", "status"}
                if key == "customer_id"
                else {
                    "order_id",
                    "customer_id",
                    "amount_minor",
                    "currency",
                    "status",
                    "delivered_at",
                    "refunded_minor",
                    "version",
                }
            )
            if not required_fields.issubset(record):
                raise FixtureDataError(f"{path.name} contains an incomplete record.")
            if key == "order_id" and (
                type(record["amount_minor"]) is not int
                or type(record["refunded_minor"]) is not int
                or type(record["version"]) is not int
                or record["version"] < 1
                or not isinstance(record["customer_id"], str)
                or not isinstance(record["currency"], str)
                or not isinstance(record["status"], str)
                or (
                    record["delivered_at"] is not None
                    and not isinstance(record["delivered_at"], str)
                )
            ):
                raise FixtureDataError(f"{path.name} contains an invalid order.")
            if key == "customer_id" and (
                not all(
                    isinstance(record[field], str)
                    for field in ("name", "email", "status")
                )
            ):
                raise FixtureDataError(f"{path.name} contains an invalid customer.")
            if record[key] in indexed:
                raise FixtureDataError(f"{path.name} contains duplicate {key} values.")
            indexed[record[key]] = record
        return indexed

    def _load_policy(self) -> dict[str, Any]:
        policy = _read_json(self.data_dir / "refund_policy.json")
        if not isinstance(policy, dict) or not {
            "policy_id",
            "version",
            "effective_from",
            "currency",
            "refund_window_days",
            "automatic_ceiling_minor",
            "required_order_status",
            "evaluation_reference_timestamp",
        }.issubset(policy):
            raise FixtureDataError("Refund policy is missing required fields.")
        if (
            type(policy["refund_window_days"]) is not int
            or policy["refund_window_days"] < 0
            or type(policy["automatic_ceiling_minor"]) is not int
            or policy["automatic_ceiling_minor"] < 0
            or not isinstance(policy["policy_id"], str)
            or not policy["policy_id"]
            or not isinstance(policy["version"], str)
            or not policy["version"]
            or not isinstance(policy["effective_from"], str)
            or not isinstance(policy["currency"], str)
            or not isinstance(policy["required_order_status"], str)
            or not isinstance(policy["evaluation_reference_timestamp"], str)
        ):
            raise FixtureDataError("Refund policy contains invalid values.")
        try:
            effective_from = datetime.fromisoformat(
                policy["effective_from"].replace("Z", "+00:00")
            )
            reference = datetime.fromisoformat(
                policy["evaluation_reference_timestamp"].replace("Z", "+00:00")
            )
        except ValueError as exc:
            logger.exception("Invalid policy timestamp.")
            raise FixtureDataError("Invalid policy timestamp.") from exc
        if (
            effective_from.tzinfo is None
            or reference.tzinfo is None
            or effective_from > reference
        ):
            raise FixtureDataError("No valid policy is active at evaluation time.")
        return policy

    @staticmethod
    def _within_refund_window(order: dict[str, Any], policy: dict[str, Any]) -> bool:
        delivered_at = order.get("delivered_at")
        if not isinstance(delivered_at, str):
            return False
        try:
            delivered = datetime.fromisoformat(delivered_at.replace("Z", "+00:00"))
            reference = datetime.fromisoformat(
                policy["evaluation_reference_timestamp"].replace("Z", "+00:00")
            )
        except (ValueError, TypeError, AttributeError) as exc:
            logger.exception("Invalid delivery or policy timestamp.")
            raise FixtureDataError("Invalid delivery or policy timestamp.") from exc
        if delivered.tzinfo is None or reference.tzinfo is None:
            raise FixtureDataError("Delivery and policy timestamps must include a timezone.")
        age_days = (reference - delivered).total_seconds() / 86400
        return 0 <= age_days <= policy["refund_window_days"]

    @staticmethod
    def _assess_eligible_action(
        amount_minor: int, policy: dict[str, Any]
    ) -> tuple[str, str, str, list[str]]:
        if amount_minor > policy["automatic_ceiling_minor"]:
            return (
                "REVIEW",
                "AUTO_CEILING_EXCEEDED",
                "HIGH",
                ["AUTO_CEILING_EXCEEDED"],
            )
        if amount_minor <= 100_000:
            risk = "LOW"
        else:
            risk = "MEDIUM"
        return "APPROVE", "ELIGIBLE", risk, [f"AMOUNT_MINOR_{amount_minor}"]


_NUMBER_IN_REQUEST = re.compile(r"(?<![A-Za-z0-9])(\d+(?:\.\d{1,2})?)(?![A-Za-z0-9])")


def scenario_amount_minor(request: str, remaining_minor: int) -> int:
    """Convert a fixture request amount from INR to paise, or use remaining balance."""
    match = _NUMBER_IN_REQUEST.search(request)
    if match is None:
        return remaining_minor
    from decimal import Decimal

    amount_minor = Decimal(match.group(1)) * 100
    if amount_minor != amount_minor.to_integral_value():
        raise ValueError("Fixture request amount cannot be represented in paise.")
    return int(amount_minor)
