"""GitHub write-access probe and recovery. Does not create tokens or a second controller."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

RECOVERY = (
    "Run gh auth status and confirm the active account.",
    "Confirm permissions.push is true for this repository.",
    "If push is false, replace the token with one that has contents write. Do not print the token.",
    "Do not create a second controller, cloud automation, or workaround repository.",
    "Re-run the master controller after access is restored.",
)


@dataclass(frozen=True)
class GitHubAccess:
    status: str
    login: str | None
    can_push: bool
    evidence: str
    recovery: tuple[str, ...]


def _run(args: list[str]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(args, check=False, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, "", str(exc)
    return completed.returncode, completed.stdout, completed.stderr


def probe_github_write(
    owner: str,
    repo: str,
    runner=_run,
) -> GitHubAccess:
    auth_code, auth_out, auth_err = runner(["gh", "api", "user"])
    if auth_code != 0:
        return GitHubAccess(
            "BLOCKED",
            None,
            False,
            auth_err.strip() or auth_out.strip() or "gh api user failed",
            RECOVERY,
        )
    try:
        login = json.loads(auth_out).get("login")
    except json.JSONDecodeError:
        return GitHubAccess("FAILED", None, False, "user payload was not JSON", RECOVERY)

    code, out, err = runner(["gh", "api", f"repos/{owner}/{repo}"])
    if code != 0:
        return GitHubAccess("BLOCKED", login, False, err.strip() or "repo lookup failed", RECOVERY)
    try:
        permissions = json.loads(out).get("permissions") or {}
    except json.JSONDecodeError:
        return GitHubAccess("FAILED", login, False, "repo payload was not JSON", RECOVERY)
    can_push = bool(permissions.get("push"))
    evidence = f"login={login} push={can_push} admin={bool(permissions.get('admin'))}"
    if not can_push:
        return GitHubAccess("BLOCKED", login, False, evidence, RECOVERY)
    return GitHubAccess("VERIFIED", login, True, evidence, ())
