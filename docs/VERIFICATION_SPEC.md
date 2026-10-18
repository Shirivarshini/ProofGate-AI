# Evidence-to-Action Contract (EAC) specification

## Contract

An EAC is a versioned structured proposal (`schema_version: 1.0`) with an agent-supplied `action_id`, `tool_name`, arguments, actor/request context, and optional candidate evidence references. Trusted backend assigns received timestamp, canonical argument hash, evidence snapshots, policy version, decision, and any authorization. Candidate references are lookup hints only.

For `refund.create`, arguments are `order_id`, `customer_id`, `amount_minor`, `currency`, and `reason`. IDs must match `^(act|ord|cus|pol|ev|ver|rev|aud|scn)_[A-Z0-9_]+$`; money is positive integer INR paise.

## Sequential verification

1. Validate Draft 2020-12 action schema and caller role.
2. Validate actor/customer context; customer may only request their own order unless staff entitlement exists.
3. Independently retrieve authoritative order, customer, and active policy.
4. Bind each action argument to evidence and record evidence version/digest.
5. Require delivered order and delivery within 30 days of fixed evaluation time `2026-10-18T00:00:00Z`.
6. Require amount no greater than remaining refundable amount.
7. Reject full-refund duplicates and any amount exceeding remaining balance.
8. Assess risk: LOW <= â‚¹1,000, MEDIUM â‚¹1,001â€“â‚¹2,000, HIGH > â‚¹2,000 or privileged/manual context.
9. Decide, create a 5-minute single-use authorization only for APPROVE, and append audit event.

## Initial synthetic policy

Automatic ceiling is â‚¹2,000 (`200000` paise). Eligible high-value refunds are `REVIEW`; they are not auto-approved. Missing/contradictory evidence is never auto-approved. Always `BLOCK`: invalid schema, unknown/cross-customer order, not delivered, expired, already fully refunded, amount <= 0, currency mismatch, amount > remaining, duplicate authorization, missing trusted record, or policy version unavailable. `REVIEW`: eligible, evidence-consistent request above ceiling or high-risk staff/manual context. `APPROVE`: eligible, evidence-consistent, same-customer request at/below ceiling.

Reason codes include `ACTION_SCHEMA_INVALID`, `CUSTOMER_AUTHORIZATION_FAILED`, `ORDER_NOT_FOUND`, `EVIDENCE_MISSING`, `EVIDENCE_CONFLICT`, `ORDER_NOT_DELIVERED`, `REFUND_WINDOW_EXPIRED`, `ALREADY_REFUNDED`, `AMOUNT_EXCEEDS_REMAINING`, `AUTO_CEILING_EXCEEDED`, `POLICY_VIOLATION`, `VERIFICATION_UNAVAILABLE`, `AUTHORIZATION_FAILURE`, and `DUPLICATE_EXECUTION_ATTEMPT`.

## Why EAC

Unlike prompt-only instructions, the contract is machine-validated and independently checked. Unlike a generic second LLM judge, it uses deterministic source-bound rules. Unlike keyword filters or basic input validation, it binds business evidence, policy versions, and execution authorization to exact action arguments. It cannot prove source correctness, cover unknown business rules, prevent a compromised trusted store, or replace human judgment for ambiguous claims.

