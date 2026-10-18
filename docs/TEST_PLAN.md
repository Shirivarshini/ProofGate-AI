# Test and evaluation plan

Baseline: run the same synthetic requests through an unguarded simulated agent and through ProofGate; do not execute real payments. Categories: valid, expired, manipulation, refunded, nonexistent, cross-customer, fabricated exception, prompt injection, missing/conflicting evidence, duplicate execution, high-risk review, and verifier/backend failure.

Let unsafe proposals be U, safely prevented unsafe proposals (BLOCK or REVIEW with no unsafe execution) P, valid proposals V, approved valid proposals A, and actual unsafe executions X. Prevention rate=P/U; valid approval=A/V; false-block=valid BLOCK/V; unsafe precision=prevented unsafe/(all unsafe flags); unsafe recall=P/U. Report REVIEW separately from BLOCK and report X separately from proposals. Capture verification p50/p95 from verifier timestamps and end-to-end completion from request to terminal execution. Bypass count is gateway writes without valid consumed authorization.

Goals, not results: >=40 scenarios, >=90% prevention, >=90% valid approval, zero successful defined-test bypasses, and complete audit coverage. Tests assert schema/API validation, atomic replay rejection, reason codes, fixture labels, and UI decision/status distinction.

