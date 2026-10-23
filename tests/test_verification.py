import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from backend.verification import CallerContext, EvidenceStore, to_api_response, verify

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "verification_proposals.json"


class VerificationScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.store = EvidenceStore.from_directory(ROOT / "data")
        schema = json.loads((ROOT / "contracts" / "verification.schema.json").read_text(encoding="utf-8"))
        cls.result_validator = Draft202012Validator(schema, format_checker=FormatChecker())

    def test_all_synthetic_scenarios_match_expected_verification(self) -> None:
        scenario_labels = json.loads((ROOT / "data" / "test_scenarios.json").read_text(encoding="utf-8"))
        proposals = self.fixtures["scenario_proposals"]
        self.assertEqual(
            [case["scenario_id"] for case in proposals],
            [scenario["scenario_id"] for scenario in scenario_labels],
        )

        for case, label in zip(proposals, scenario_labels, strict=True):
            with self.subTest(scenario_id=case["scenario_id"]):
                self.assertEqual(case["expected_decision"], label["expected_decision"])
                self.assertEqual(case["expected_reason_codes"], label["expected_reason_codes"])
                result = verify(case["action"], CallerContext(**case["caller"]), self.store)
                self.assertEqual(result["decision"], case["expected_decision"])
                self.assertEqual(result["reason_codes"], case["expected_reason_codes"])
                self.assertEqual(result["action_id"], case["action"]["action_id"])
                self.assertEqual(result["verified_at"], "2026-10-18T00:00:00Z")
                self.assertEqual(list(self.result_validator.iter_errors(result)), [])

    def test_api_adapter_maps_schema_result_without_merging_risk_shape(self) -> None:
        case = self.fixtures["scenario_proposals"][0]
        result = verify(case["action"], CallerContext(**case["caller"]), self.store)

        response = to_api_response(result)

        self.assertEqual(response["verification_decision"], result["decision"])
        self.assertEqual(response["risk_level"], result["risk_assessment"]["level"])
        self.assertEqual(response["execution_status"], "NOT_STARTED")
        self.assertNotIn("decision", response)
        self.assertNotIn("risk_assessment", response)
        self.assertNotIn("authorization_id", result)


if __name__ == "__main__":
    unittest.main()
