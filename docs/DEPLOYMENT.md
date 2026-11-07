# Deployment, Backup, and Rollback Procedures

## Promotion model

1. Merge to `main` after approved pull request and passing checks.
2. Deploy first to `staging` environment.
3. Validate pathway health in staging.
4. Promote to `production` with protected environment approval.

## Safe deployment requirements

- No direct deployment from unreviewed branches.
- All CI and security checks must pass before deploy.
- Production deployments require manual approval in GitHub Environments.
- Deployments must be idempotent and produce auditable logs.

## Backup procedure

Before production deployment:

1. Snapshot persistent state (database dump or storage backup).
2. Record release identifier and backup reference.
3. Verify backup integrity before continuing.

## Rollback procedure

If production validation fails:

1. Stop further traffic shift or release progression.
2. Redeploy previous known-good release.
3. Restore data snapshot if schema/data changes are incompatible.
4. Record incident timeline and corrective actions in postmortem.
