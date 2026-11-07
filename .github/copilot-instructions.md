# ULTRON Master Operating Rules

## Mission priorities

1. Deliver a secure, tested, maintainable repository foundation.
2. Deliver complete payment-to-delivery revenue pathways with verifiable outcomes.
3. Expand into the full ULTRON operating system through modular, validated increments.

## Non-negotiable execution rules

- Never expose credentials, secrets, or personal information in code, logs, docs, or CI output.
- Never commit directly to `main`; all changes must be made on feature branches via pull requests.
- Never claim tests, integrations, or deployments succeeded unless verified by actual evidence.
- Never mark placeholder or mock-only functionality as production-ready.
- Never bypass security checks, code review, or environment protections.

## Engineering standards

- Every change must include automated validation appropriate to the current stack.
- Failures must be explicit, actionable, and observable.
- Security and reliability controls are required for each new subsystem.
- Use environment separation (`development`, `staging`, `production`) with controlled promotion.
- Maintain backup and rollback procedures for all state-changing deployments.

## Documentation requirements

- Update architecture, audit, and execution status documents with each meaningful change.
- Record verified evidence for completion claims.
- Track known risks and unresolved blockers until closed.
