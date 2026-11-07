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
