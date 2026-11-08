# Master controller

`ultron/controller.py` is the only master. Payments, fulfilment, and the event log report through `ultron/modules.py`. They do not schedule themselves.

One cycle:

1. Wake and open the database.
2. Probe GitHub write access (`ultron/github_access.py`).
3. Collect subordinate reports.
4. Choose one next action.
5. Refuse any change that is not on the allowlist and approved.
6. Measure closed, reconciled orders only.
7. Store the cycle. A repeated cycle key returns the stored report.
8. Stop. The next cycle is a new run, not a second controller.

A recorded cycle is not a deployment, a sale, or a settled profit. `deployed` is always false in this build. `forecast_cents` is always null.

GitHub write access in this session was checked with the API: account `cloyboy0904360-ai` has `push` and `admin` on `cloyboy0904360-ai/Ultron`. That does not mean the scheduled workflow can push. `.github/workflows/controller.yml` is read-only until an owner approves `contents: write`. The workflow file has not run.

Copilot cloud automations cannot be created in this public repository. None was created, so there is no competing master scenario.

A 15-minute Make trigger was not created. `MAKE_API_KEY` is absent, and a second scheduler would compete with this controller. The only wake file is `.github/workflows/controller.yml`. It has not run.

GitHub permissions checked independently on 2026-11-08:

- Read: `GET contents/README.md` returned `README.md`.
- Write: created `refs/heads/ultron-write-probe-20261108` and deleted it. A later GET returned 404.
- Branch: `feature/payment-verification-and-registries` exists.
- Commit: `884b7f7fd6bb401c3123c42f808fe68e4839b388` was readable.
- Pull request: PR 23 is open.

`permissions.push` and `permissions.admin` are true for this token. That is not a connected payment, supplier, or Make account.

Recovery when write access fails is the five steps in `ultron/github_access.py`. The controller assigns that recovery to GUARDIAN and applies no change.
