# Shared data schemas

All timestamps are RFC 3339 UTC strings. IDs use `prefix_UPPER_SNAKE`; nullable fields are explicitly `null`; absent optional fields are not inferred. Money is integer minor units (`amount_minor`) and `currency` is ISO 4217 `INR`; no floating point. Schema version is `1.0`.

| Model | Required fields | Meaning / rules | Relationships |
|---|---|---|---|
| Customer | customer_id, name, email, status | fictional identity; email format; status ACTIVE/INACTIVE | owns orders |
| Order | order_id, customer_id, amount_minor, currency, status, delivered_at, refunded_minor, version | status DELIVERED/PROCESSING/CANCELLED; nonnegative totals | belongs to customer |
| Refund Policy | policy_id, version, effective_from, refund_window_days, automatic_ceiling_minor, currency | active versioned authoritative rule | evidence for verification |
| Agent Action | action_id, schema_version, tool_name, arguments, actor_context | contract schema validates strict properties | links order/customer |
| Evidence Reference | evidence_id, source_type, source_id | agent hint; untrusted | resolved by verifier |
| Verified Evidence | evidence_id, source_type, source_id, version, retrieved_at, digest | trusted snapshot; digest required | attached to result |
| Verification Result | verification_id, action_id, decision, risk_level, reason_codes, evidence, execution_status | decisions APPROVE/BLOCK/REVIEW | one action; optional authorization |
| Risk Assessment | level, factors | LOW/MEDIUM/HIGH; factors are stable codes | embedded in result |
| Human Review | review_id, action_id, status, outcome | PENDING/RESOLVED; outcome APPROVED/REJECTED nullable only when pending | review action |
| Audit Event | audit_id, action_id, event_type, occurred_at, payload | append-only; payload redacted | records lifecycle |
| Test Scenario | scenario_id, description, request, customer_id, order_id, expected_decision, expected_execution_status, expected_reason_codes, safety, category | deterministic expected label | points to fixtures |

Examples: `{"customer_id":"cus_001","name":"Asha Rao","email":"asha.rao@example.test","status":"ACTIVE"}`; `{"order_id":"ord_001","customer_id":"cus_001","amount_minor":129900,"currency":"INR","status":"DELIVERED","delivered_at":"2026-10-05T10:00:00Z","refunded_minor":0,"version":1}`; `{"verification_id":"ver_001","action_id":"act_001","decision":"APPROVE","risk_level":"MEDIUM","reason_codes":["ELIGIBLE"],"evidence":[],"execution_status":"NOT_STARTED"}`.

Enumeration summary: decision `APPROVE|BLOCK|REVIEW`; risk `LOW|MEDIUM|HIGH`; execution `NOT_STARTED|PENDING_REVIEW|EXECUTED|FAILED|NOT_EXECUTED`; review outcome `APPROVED|REJECTED`.

