"""Composio session setup for ULTRON.

Credentials are read only from environment variables. Never commit API keys.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

COMPOSIO_API_BASE = "https://backend.composio.dev/api/v3.1"
DEFAULT_SESSION_CONFIG_ID = "sc_bwsfGt3WWy_s"
DEFAULT_USER_ID = "cloyboy0904360-ai"


def _apply_session_config(
    session_id: str,
    api_key: str,
    session_config_id: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Apply the saved Composio session config using the v3.1 PATCH endpoint."""
    url = f"{COMPOSIO_API_BASE}/tool_router/session/{session_id}"
    payload = json.dumps(
        {"experimental": {"session_config_id": session_config_id}}
    ).encode("utf-8")
    request = Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Composio session config update failed (HTTP {exc.code}): {detail}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Composio session config update failed: {exc}") from exc


def create_or_resume_session(
    *,
    api_key: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    session_config_id: str | None = None,
):
    """Create or resume a Composio session and apply ULTRON's saved config.

    Environment:
      COMPOSIO_API_KEY                 Required project API key.
      ULTRON_COMPOSIO_USER_ID          Stable ULTRON user identifier.
      ULTRON_COMPOSIO_SESSION_ID       Existing session ID (optional).
      COMPOSIO_SESSION_CONFIG_ID       Saved session config ID (optional).
    """
    resolved_api_key = api_key or os.getenv("COMPOSIO_API_KEY")
    if not resolved_api_key:
        raise RuntimeError(
            "COMPOSIO_API_KEY is not set. Add it to the runtime environment; "
            "do not put the key in source control."
        )

    resolved_user_id = user_id or os.getenv(
        "ULTRON_COMPOSIO_USER_ID", DEFAULT_USER_ID
    )
    resolved_session_id = session_id or os.getenv("ULTRON_COMPOSIO_SESSION_ID")
    resolved_config_id = (
        session_config_id
        or os.getenv("COMPOSIO_SESSION_CONFIG_ID")
        or DEFAULT_SESSION_CONFIG_ID
    )

    from composio import Composio

    client = Composio(api_key=resolved_api_key)
    session = (
        client.use(resolved_session_id)
        if resolved_session_id
        else client.sessions.create(user_id=resolved_user_id)
    )
    _apply_session_config(
        session.session_id,
        resolved_api_key,
        resolved_config_id,
    )
    return session
