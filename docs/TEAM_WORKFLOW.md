# Team workflow

Branches: `main`, `feature/agent-backend` (Member 1), `feature/verification-engine` (Member 2), and `feature/frontend-dashboard` (Member 3). Ownership is backend/agent/gateway; EAC/policy/risk/tests; and frontend/fixtures/docs respectively.

Use small descriptive commits and pull requests into main. Before merge, affected owner reviews, CI/schema tests pass, contract changes are approved by all affected owners, and integration blockers are posted immediately. Rebase/merge conflicts are resolved by the owner of the changed component; never overwrite teammate work. Credentials and real data are prohibited. Mock behavior must be labeled and no test outcome may be invented.

Each branch begins by reading `AGENTS.md` and shared contracts. Codex prompts must name the branch scope, cite the contract version, ask it to inspect before editing, and require validation output. Contract changes use a dedicated PR updating schemas, OpenAPI, docs, fixtures, and migration notes together.

