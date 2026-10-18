# Seven-day implementation plan

| Day | Member 1 | Member 2 | Member 3 | Checkpoint / done / fallback |
|---|---|---|---|---|
| 1 | app/persistence skeleton | approve EAC rules | fixtures/docs | contracts signed; use JSON fixtures if DB slips |
| 2 | agent adapter baseline | verifier skeleton | Vite shell | proposal reaches stub verifier; use deterministic agent stub |
| 3 | protected gateway | trusted lookup/policy | playground UI | valid/invalid paths wired; correctness over polish |
| 4 | orchestration | review state | review/audit screens | review resolves and gateway rechecks state |
| 5 | metrics plumbing | adversarial evaluation | results views | >=40 planned cases; run only completed tests |
| 6 | reliability/error handling | latency/audit analysis | abstract/diagram | demo rehearsal; static screenshots fallback |
| 7 | integration/QA | security regression | demo polish | terminal flows pass; reduce scope rather than bypass gate |

Dependencies: Day 1 contracts unblock all; verifier/gateway correctness is critical path (Days 2â€“4). UI and fixtures proceed in parallel after Day 1. Definition of done each day: owner PR reviewed, relevant tests run, limitations documented. Main risk is integration drift; mitigate with daily contract checkpoint and fixture-driven tests.

