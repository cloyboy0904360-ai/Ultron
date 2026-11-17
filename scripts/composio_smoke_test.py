"""Make a read-only GitHub tool call through ULTRON's Composio session."""

from __future__ import annotations

import json
import os
import sys

from ultron.composio_client import create_or_resume_session


def main() -> int:
    try:
        session = create_or_resume_session()
        result = session.execute(
            "GITHUB_GET_REPOSITORY_CONTENT",
            arguments={
                "owner": "cloyboy0904360-ai",
                "repo": "ULTRON",
                "path": "",
            },
            account=os.getenv("ULTRON_COMPOSIO_GITHUB_ACCOUNT", "Ultron GitHub"),
        )
        if result.result_type != "completed":
            raise RuntimeError(
                result.error or f"Composio tool call ended as {result.result_type}"
            )

        data = result.data or {}
        content = data.get("content", []) if isinstance(data, dict) else []
        names = sorted(
            item.get("name", "")
            for item in content
            if isinstance(item, dict) and item.get("name")
        )
        print(
            json.dumps(
                {
                    "status": "VERIFIED",
                    "tool": "GITHUB_GET_REPOSITORY_CONTENT",
                    "repository": "cloyboy0904360-ai/ULTRON",
                    "root_entries": names,
                    "session_id": session.session_id,
                },
                indent=2,
            )
        )
        print(
            "\nSave this value as ULTRON_COMPOSIO_SESSION_ID for later runs: "
            f"{session.session_id}"
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary reports provider failures cleanly.
        print(f"Composio smoke test FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
