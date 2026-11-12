"""GitHub Issues-backed durable queue for ULTRON workers (stdlib only)."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class GitHubAPIError(RuntimeError):
    pass


class GitHubQueue:
    def __init__(self, token: str, repository: str, api_url: str = "https://api.github.com"):
        if not token or "/" not in repository:
            raise ValueError("GITHUB_TOKEN and owner/repository are required")
        self.token = token
        self.repository = repository
        self.api_url = api_url.rstrip("/")

    @classmethod
    def from_environment(cls) -> GitHubQueue:
        return cls(
            token=os.environ.get("GITHUB_TOKEN", ""),
            repository=os.environ.get("GITHUB_REPOSITORY", ""),
            api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
        )

    def _request(self, method: str, path: str, payload: Any = None) -> Any:
        url = f"{self.api_url}/repos/{self.repository}{path}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = urllib.request.Request(
                url, data=body, method=method,
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {self.token}",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "Content-Type": "application/json",
                    "User-Agent": "ULTRON-GitHub-Agent-Runtime",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    raw = response.read()
                    return json.loads(raw.decode("utf-8")) if raw else None
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise GitHubAPIError(f"GitHub API returned {exc.code}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise GitHubAPIError(f"GitHub API request failed: {exc}") from exc
        raise GitHubAPIError("GitHub API request exhausted retries")

    def _paginated_get(self, path: str) -> list[dict[str, Any]]:
        """Read every page; fail closed rather than return a truncated history."""
        records: list[dict[str, Any]] = []
        seen: set[tuple[str, Any]] = set()
        page = 1
        while True:
            separator = "&" if "?" in path else "?"
            result = self._request(
                "GET", f"{path}{separator}per_page=100&page={page}"
            )
            if not isinstance(result, list):
                raise GitHubAPIError("GitHub paginated endpoint returned a non-list response")
            for item in result:
                if not isinstance(item, dict):
                    raise GitHubAPIError("GitHub paginated endpoint returned an invalid record")
                identifier = item.get("id", item.get("number"))
                key = ("record", identifier) if identifier is not None else ("page", (page, len(records)))
                if key not in seen:
                    seen.add(key)
                    records.append(item)
            if len(result) < 100:
                return records
            page += 1

    def list_issues(self, agent: str, status: str) -> list[dict[str, Any]]:
        labels = urllib.parse.quote(f"agent:{agent.lower()},status:{status.lower()}", safe=",")
        issues = self._paginated_get(f"/issues?state=open&labels={labels}")
        trusted = {"OWNER", "COLLABORATOR", "MEMBER"}
        return [
            item
            for item in issues
            if "pull_request" not in item and item.get("author_association") in trusted
        ]

    def comments(self, issue_number: int) -> list[dict[str, Any]]:
        return self._paginated_get(f"/issues/{issue_number}/comments")

    def add_comment(self, issue_number: int, body: str) -> None:
        self._request("POST", f"/issues/{issue_number}/comments", {"body": body})

    def set_status(self, issue: dict[str, Any], status: str) -> None:
        labels = [label["name"] for label in issue.get("labels", [])]
        labels = [name for name in labels if not name.startswith("status:")]
        labels.append(f"status:{status.lower()}")
        self._request("PATCH", f"/issues/{issue['number']}", {"labels": labels})
