# Security Policy

## Supported security posture

This repository is actively hardened through CI validation, secret scanning, dependency checks, and required pull-request workflows.

## Reporting a vulnerability

If you discover a vulnerability:

1. **Do not** open a public issue with exploit details.
2. Report privately through GitHub security advisories (preferred) or repository maintainers via private channel.
3. Include affected files, impact, reproduction steps, and proposed remediation if available.

We will acknowledge reports promptly, validate impact, and coordinate responsible disclosure.

## Security requirements

- No credentials, tokens, API keys, or personal data may be committed.
- All changes must pass CI, security scanning, and review before merge.
- Dependency risks must be reviewed and remediated before production promotion.
- Production changes must be reversible through documented rollback procedures.
- Environment configs must contain no secrets; use secure secret stores for runtime credentials.
