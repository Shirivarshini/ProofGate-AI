# ProofGate AI agent rules

1. Read `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.yaml`, `docs/DATA_SCHEMAS.md`, and `docs/VERIFICATION_SPEC.md` before changing implementation.
2. Respect ownership: Member 1 backend/agent/gateway; Member 2 verification/policy/tests; Member 3 frontend/fixtures/docs.
3. Implement only against the shared OpenAPI and JSON Schemas. Propose, review, and document shared-contract changes before applying them.
4. Never add a path that bypasses verification for a protected write. Frontend controls must call orchestrating APIs, never tools directly.
5. Keep mock behavior visibly labeled; do not present it as Gemini inference, verified evidence, or executed money movement.
6. Preserve APPROVE (verification) versus EXECUTED (execution) as separate states.
7. Run relevant tests and schema/API validation after changes. Do not fabricate results.
8. Document changed assumptions, limitations, and migration requirements in the relevant docs or PR.
9. Never commit credentials, real customer data, or payment credentials.
10. Stop and report contract conflicts, missing requirements, or security-impacting ambiguity before affected implementation.

