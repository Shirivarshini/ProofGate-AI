# Foundation review

Created: root guidance/security files; PRD, architecture, API, schemas, verification, UI, test, workflow, and implementation documents; three Draft 2020-12 contracts; synthetic customers, orders, policy, and 20 scenarios. `frontend/`, `backend/`, and `tests/` are intentionally reserved and contain no application placeholders.

Final decisions: INR paise integers; fixed evaluation time `2026-10-18T00:00:00Z`; 30-day window; â‚¹2,000 automatic ceiling; exact short-lived single-use authorization; mandatory failures BLOCK; eligible high value REVIEW. API decisions/execution statuses and schema enums are aligned.

Open questions: final authentication provider/roles, persistence choice, authorization-token transport, and reviewer identity model. Risks: synthetic policy is not legal/business policy; trusted store compromise and ambiguous evidence remain outside rule guarantees; no runtime implementation has been security-tested.

Readiness: ready for parallel development once the team confirms these open choices. Validation should be rerun after any contract change.

Validation performed: all seven JSON documents parsed successfully; all three contracts passed `jsonschema.Draft202012Validator.check_schema`; API YAML parsed with PyYAML and all seven required paths were found. Cross-check confirmed the shared decision, risk, execution, and review enums. Fixture totals are 10 customers, 20 orders, one policy, and 20 labeled scenarios. Full OpenAPI semantic linting was not run because no OpenAPI linter is configured in this foundation-only workspace.

