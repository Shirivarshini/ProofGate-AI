import json
import unittest
from pathlib import Path

from backend.verification import EvidenceStore
from backend.verification.evaluation import compare_guarded_to_baseline

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "verification_proposals.json"


class VerificationEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.store = EvidenceStore.from_directory(ROOT / "data")

    def test_scenario_evaluation_compares_gate_with_unverified_baseline(self) -> None:
        cases = self.fixtures["scenario_proposals"]

        report = compare_guarded_to_baseline(cases, self.store)

        unsafe_count = sum(case["safety"] == "UNSAFE" for case in cases)
        valid_count = len(cases) - unsafe_count
        prevented_count = sum(
            case["safety"] == "UNSAFE" and case["expected_decision"] in {"BLOCK", "REVIEW"}
            for case in cases
        )
        valid_approved_count = sum(
            case["safety"] == "SAFE" and case["expected_decision"] == "APPROVE"
            for case in cases
        )
        self.assertEqual(report["case_count"], 20)
        self.assertEqual(report["baseline_unsafe_proposals_would_execute"], unsafe_count)
        self.assertEqual(report["guard_prevented_unsafe_proposals"], prevented_count)
        self.assertEqual(report["guard_valid_proposals_approved"], valid_approved_count)
        self.assertEqual(report["prevention_rate"], prevented_count / unsafe_count)
        self.assertEqual(report["valid_approval_rate"], valid_approved_count / valid_count)
        self.assertFalse(report["execution_performed"])
        self.assertTrue(all(case["baseline"] == "WOULD_EXECUTE_UNVERIFIED" for case in report["cases"]))

    def test_total_structured_case_set_exceeds_forty_without_changing_shared_scenarios(self) -> None:
        scenario_ids = {
            case["scenario_id"] for case in self.fixtures["scenario_proposals"]
        }
        adversarial_ids = {
            case["scenario_id"] for case in self.fixtures["adversarial_proposals"]
        }

        self.assertEqual(len(scenario_ids), 20)
        self.assertEqual(len(adversarial_ids), 25)
        self.assertEqual(len(scenario_ids | adversarial_ids), 45)

    def test_empty_evaluation_has_undefined_rates(self) -> None:
        report = compare_guarded_to_baseline([], self.store)

        self.assertEqual(report["case_count"], 0)
        self.assertIsNone(report["prevention_rate"])
        self.assertIsNone(report["valid_approval_rate"])


if __name__ == "__main__":
    unittest.main()
