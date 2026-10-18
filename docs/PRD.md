# Product requirements

## Definition

Vision: make AI-proposed actions accountable before they affect systems. Target users are support operators, reviewers, and hackathon evaluators. Today, an agent may call a refund tool based on generated text without independently checking order facts. ProofGate supplies source-bound, deterministic intervention rather than a second agent's opinion.

## Functional requirements and acceptance

| ID | Requirement | Testable acceptance criterion |
|---|---|---|
| FR-001 | Submit a support request | Authenticated request produces a unique action ID or validation error. |
| FR-002 | Generate structured proposal | Proposal validates against `action.schema.json`; malformed fields return `INVALID_ACTION_SCHEMA`. |
| FR-003 | Intercept protected action | No agent/UI path invokes refund storage except gateway. |
| FR-004 | Retrieve trusted evidence | Result contains independently retrieved order/customer/policy versions or fails closed. |
| FR-005 | Check authorization/policy | Cross-customer, expired, undelivered, duplicate, or overbalance case is BLOCK. |
| FR-006 | Assess risk | Eligible >â‚¹2,000 case is HIGH and REVIEW. |
| FR-007 | Return decision | API exposes enumerated decision and separate execution status. |
| FR-008 | Execute approved action | Gateway accepts exact unexpired authorization once and atomically rechecks balance. |
| FR-009 | Human review | Eligible pending review can be APPROVED/REJECTED once; mandatory block cannot be overridden. |
| FR-010 | Audit trail/UI | Every lifecycle event is queryable and dashboard displays evidence/reasons. |
| FR-011 | Baseline evaluation | Same labeled scenarios run with baseline and guarded modes without fabricated results. |

## Non-functional requirements

Security: fail closed, least privilege, no real payments/PII. Reliability: idempotent gateway and durable audit. Explainability: stable reason codes and evidence versions. Performance: record p50/p95 verification latency; no unverified latency promise. Reproducibility: fixed fixtures/reference time. Accessibility: keyboard, semantic labels, contrast. Maintainability: versioned schemas, small services, documented contracts.

## Scope

Must-have: one refund action, synthetic data, evidence/policy checks, three decisions, gateway model, review, audit, dashboard read views, baseline plan. Stretch: red-team suite and model routing. Excluded: real payments, production deployment, multiple domains, complex multi-agent orchestration, custom training, and unnecessary infrastructure.

