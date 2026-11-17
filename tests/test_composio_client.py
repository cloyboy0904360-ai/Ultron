from __future__ import annotations

import json
from urllib.request import Request

import pytest

from ultron import composio_client


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"session_id":"trs_test","config_version":1}'


def test_apply_session_config_patches_v31_config(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(composio_client, "urlopen", fake_urlopen)

    result = composio_client._apply_session_config(
        "trs_test", "test-key", "sc_test"
    )

    request = captured["request"]
    assert isinstance(request, Request)
    assert request.full_url.endswith("/tool_router/session/trs_test")
    assert request.get_method() == "PATCH"
    assert request.get_header("X-api-key") == "test-key"
    assert json.loads(request.data) == {
        "experimental": {"session_config_id": "sc_test"}
    }
    assert result["session_id"] == "trs_test"


def test_create_session_requires_api_key(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="COMPOSIO_API_KEY is not set"):
        composio_client.create_or_resume_session()
