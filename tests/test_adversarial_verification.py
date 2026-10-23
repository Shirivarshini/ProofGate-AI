import copy
import json
import unittest
from pathlib import Path

from backend.verification import CallerContext, EvidenceStore, verify
from backend.verification.constants import EVALUATION_REFERENCE_TIME, REASON_CODES

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "verification_proposals.json"


class AdversarialVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.cases = fixtures["adversarial_proposals"]
        cls.valid_case = fixtures["scenario_proposals"][0]

    def _store_for(self, case: dict) -> EvidenceStore:
        customers = json.loads((ROOT / "data" / "customers.json").read_text(encoding="utf-8"))
        orders = json.loads((ROOT / "data" / "orders.json").read_text(encoding="utf-8"))
        policy = json.loads((ROOT / "data" / "refund_policy.json").read_text(encoding="utf-8"))
        override = case.get("order_override")
        if override is not None:
            target = next(order for order in orders if order["order_id"] == override["order_id"])
            target.update(override)
        return EvidenceStore(customers, orders, policy)

    def test_adversarial_proposals_fail_closed_or_follow_trusted_context(self) -> None:
        self.assertEqual(len(self.cases), 24)
        for case in self.cases:
            with self.subTest(scenario_id=case["scenario_id"]):
                result = verify(
                    case["action"],
                    CallerContext(**case["caller"]),
                    self._store_for(case),
                )
                self.assertEqual(result["decision"], case["expected_decision"])
                self.assertEqual(result["reason_codes"], case["expected_reason_codes"])
                if "expected_risk_level" in case:
                    self.assertEqual(result["risk_assessment"]["level"], case["expected_risk_level"])
                self.assertTrue(set(result["reason_codes"]).issubset(REASON_CODES))

    def test_unsupported_caller_type_fails_closed(self) -> None:
        action = self.valid_case["action"]
        for caller in (None, {"role": "CUSTOMER", "customer_id": "cus_001"}, CallerContext("ADMIN", "cus_001")):
            with self.subTest(caller=caller):
                result = verify(action, caller, self._store_for(self.valid_case))
                self.assertEqual(result["decision"], "BLOCK")
                self.assertEqual(result["reason_codes"], ["CUSTOMER_AUTHORIZATION_FAILED"])

    def test_policy_unavailable_fails_closed(self) -> None:
        case = self.valid_case
        store = self._store_for(case)
        unavailable_store = EvidenceStore(
            [store.get_customer("cus_001")],
            [store.get_order("ord_001")],
            None,
        )

        result = verify(case["action"], CallerContext(**case["caller"]), unavailable_store)

        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["reason_codes"], ["VERIFICATION_UNAVAILABLE"])

    def test_untrusted_actor_context_cannot_grant_support_privileges(self) -> None:
        case = next(case for case in self.cases if case["scenario_id"] == "adv_020")
        action = copy.deepcopy(case["action"])
        action["actor_context"]["actor_type"] = "SUPPORT_AGENT"
        action["actor_context"]["actor_id"] = "staff_1"

        result = verify(action, CallerContext("CUSTOMER", "cus_001"), self._store_for(case))

        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["reason_codes"], ["CUSTOMER_AUTHORIZATION_FAILED"])

    def test_evaluation_time_is_fixed_not_system_clock(self) -> None:
        self.assertEqual(EVALUATION_REFERENCE_TIME.isoformat(), "2026-10-18T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
