from collections.abc import Iterable
from typing import Any

from .engine import CallerContext, verify
from .evidence import EvidenceStore


def compare_guarded_to_baseline(
    cases: Iterable[dict[str, Any]],
    evidence_store: EvidenceStore | None = None,
) -> dict[str, Any]:
    evaluated: list[dict[str, Any]] = []
    unsafe_count = 0
    valid_count = 0
    prevented_unsafe_count = 0
    unsafe_approved_count = 0
    valid_approved_count = 0

    for case in cases:
        case_id = case.get("scenario_id")
        safety = case.get("safety")
        action = case.get("action")
        caller_data = case.get("caller")
        if (
            not isinstance(case_id, str)
            or not isinstance(safety, str)
            or safety not in {"SAFE", "UNSAFE"}
            or not isinstance(action, dict)
            or not isinstance(caller_data, dict)
        ):
            raise ValueError("Each evaluation case requires scenario_id, safety, action, and caller")
        caller = CallerContext(
            role=caller_data.get("role"),
            customer_id=caller_data.get("customer_id"),
        )
        verification = verify(action, caller, evidence_store)
        unsafe = safety == "UNSAFE"
        unsafe_count += int(unsafe)
        valid_count += int(not unsafe)
        prevented = unsafe and verification["decision"] in {"BLOCK", "REVIEW"}
        prevented_unsafe_count += int(prevented)
        unsafe_approved_count += int(unsafe and verification["decision"] == "APPROVE")
        valid_approved_count += int(not unsafe and verification["decision"] == "APPROVE")

        evaluated.append(
            {
                "scenario_id": case_id,
                "baseline": "WOULD_EXECUTE_UNVERIFIED",
                "verification_decision": verification["decision"],
                "execution_status": verification["execution_status"],
                "reason_codes": verification["reason_codes"],
                "unsafe_proposal": unsafe,
                "prevented_by_gate": prevented,
            }
        )

    return {
        "case_count": len(evaluated),
        "baseline_unsafe_proposals_would_execute": unsafe_count,
        "guard_prevented_unsafe_proposals": prevented_unsafe_count,
        "guard_unsafe_proposals_approved": unsafe_approved_count,
        "guard_valid_proposals_approved": valid_approved_count,
        "prevention_rate": prevented_unsafe_count / unsafe_count if unsafe_count else None,
        "valid_approval_rate": valid_approved_count / valid_count if valid_count else None,
        "cases": evaluated,
        "execution_performed": False,
    }
