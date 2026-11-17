# ULTRON Composio integration

ULTRON uses the Composio Python SDK and Composio Tool Router sessions. The session
config ID supplied for this project is applied through the Composio v3.1 PATCH
endpoint after a session is created or resumed.

## Required configuration

Set these environment variables in the environment that runs ULTRON:

- `COMPOSIO_API_KEY`: required Composio project API key. Store it as a secret.
- `ULTRON_COMPOSIO_USER_ID`: stable ULTRON user identifier. Defaults to
  `cloyboy0904360-ai`; use the same value on later runs.
- `ULTRON_COMPOSIO_SESSION_ID`: optional existing session ID. Set this after
  the first successful run so ULTRON resumes the same persistent session.
- `COMPOSIO_SESSION_CONFIG_ID`: optional override for the saved session config.
  Defaults to the supplied `sc_bwsfGt3WWy_s` value.
- `ULTRON_COMPOSIO_GITHUB_ACCOUNT`: optional connected-account alias. Defaults
  to `Ultron GitHub`.

Never put API keys or connected-account secrets in source files, commits, logs,
or issue descriptions.

## First real tool call

Install the project dependencies, then run:

```bash
python -m pip install -e .
python scripts/composio_smoke_test.py
```

The smoke test performs a read-only `GITHUB_GET_REPOSITORY_CONTENT` call against
the ULTRON repository. It prints the root entries and the new session ID. Save
that ID in `ULTRON_COMPOSIO_SESSION_ID` before the next run.

If the saved session config does not permit GitHub, or the selected Composio
user has no active GitHub connection, the tool call will fail with the provider
error. Do not bypass the saved policy; correct the Composio session config or
complete the GitHub connection first.

## GitHub Actions

Add `COMPOSIO_API_KEY` as a repository Actions secret before running this
smoke test in CI. Add `ULTRON_COMPOSIO_SESSION_ID` as a variable only after a
session has been created and verified. Do not print the API key in workflow logs.

## Local verification

```bash
pytest -q
ruff check .
python scripts/validate_repository.py
```
