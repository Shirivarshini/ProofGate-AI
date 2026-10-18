# ProofGate AI

**Every AI Action. Verified Before Execution.**

ProofGate AI is a Stage 0 foundation for Perceptron Hackathon 2026 (IIT Bombay Ã— Optiver) PS 9: *Catching an Agent Before It Acts on a Bad Idea*. It defines an independent evidence-grounded gate between an AI agent and protected tools.

## Problem and solution

Autonomous agents can hallucinate policy, misuse customer data, or propose unsupported actions. ProofGate intercepts a structured tool proposal, independently retrieves trusted records, evaluates deterministic policy and risk rules, and returns `APPROVE`, `BLOCK`, or `REVIEW`. Only an approved exact, short-lived authorization can reach the protected execution gateway.

The core design is an **Evidence-to-Action Contract (EAC)**: an action must satisfy explicit evidence requirements; agent rationale, references, and confidence are never trusted on their own. The MVP is a synthetic customer-support refund domain.

## MVP features

- Order lookup and refund proposals
- Trusted-record and refund-policy verification
- Risk-adaptive approve/block/review routing
- Single-use protected refund execution authorization
- Human review and explainable audit history
- Reproducible synthetic fixtures and adversarial evaluation plan

## Architecture and stack

Planned stack: React + Vite + JavaScript/JSX + Tailwind + React Router + Axios + Lucide React; FastAPI + Python; Gemini API behind an agent adapter; a local relational database for MVP persistence. See [Architecture](docs/ARCHITECTURE.md) and [API contract](docs/API_CONTRACT.yaml). Stage 0 does **not** implement these features.

## Repository map

```text
docs/       product, architecture, contract, UI, test, and delivery specifications
contracts/  Draft 2020-12 machine-readable shared schemas
data/       synthetic customers, orders, policy, and test scenarios
frontend/   reserved for Member 3 implementation
backend/    reserved for Members 1â€“2 implementation
tests/      reserved for automated tests
```

## Team ownership

| Member | Primary ownership |
|---|---|
| 1 | Agent orchestration, FastAPI, persistence, gateway, integration |
| 2 | EAC, evidence/policy/risk checks, evaluation |
| 3 | React UX, synthetic data, documentation, diagrams |

## Seven-day roadmap

Day 1 contracts and fixtures; Day 2 skeletons; Day 3 trusted verification and gateway; Day 4 integration/reviews; Day 5 adversarial evaluation; Day 6 reliability and submission assets; Day 7 QA and demo. Details: [implementation plan](docs/IMPLEMENTATION_PLAN.md).

## Status and setup

**Current status: Stage 0 complete as documentation, contracts, and synthetic fixtures only.** No backend, agent, dashboard, payment integration, deployment, or evaluation result is claimed implemented.

Future implementers: copy `.env.example` to `.env`, supply only development credentials, read `AGENTS.md`, then implement only against the OpenAPI and JSON-schema contracts. Do not commit `.env`.

## Security principles

Protected writes are gateway-only; verification fails closed; agent evidence is untrusted until independently retrieved; authorization is single-use and bound to exact arguments/evidence; mutable state is rechecked at commit; UI never executes protected operations directly.

## Round 1 alignment

The foundation supports the mandatory 600â€“900 word technical abstract and optional one-page architecture diagram. It is designed to demonstrate a checker that catches a deliberately bad refund action before execution; a working MVP is not claimed for Round 1.

