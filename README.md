# ULTRON

Secure, testable foundation for the ULTRON operating system.

## Current scope

- Harden repository governance, security controls, and CI validation.
- Provide one complete **payment-to-delivery revenue pathway** with automated tests.
- Establish development, staging, and production separation with safe deployment procedures.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
pytest -q
ruff check .
python scripts/validate_repository.py
```

## Repository structure

- `ultron/` core Python modules for the current pathway implementation
- `tests/` automated tests
- `docs/` architecture, audit, execution status, and deployment procedures
- `.github/workflows/` CI, security scanning, and deployment controls
- `config/environments/` environment-specific non-secret configuration

## Operations control documents

- `docs/MASTER_CONTROL_DASHBOARD.md`
- `docs/ASSET_AUDIT.md`
- `docs/TASK_REGISTER.md`
- `docs/AGENT_NETWORK.md`
- `docs/CORE_RELEASE_GATE.md`
