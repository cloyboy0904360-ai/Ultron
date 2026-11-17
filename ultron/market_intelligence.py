"""Evidence-first technology and market signal collection for ULTRON."""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

USER_AGENT = "ULTRON-Market-Intelligence/1.0 (+https://github.com/cloyboy0904360-ai/Ultron)"
DEFAULT_SOURCES = {
    "Hacker News": "https://news.ycombinator.com/rss",
    "GitHub Trending": "https://github.com/trending",
}
HIGH_VALUE_TERMS = {
    "automation", "agent", "agents", "ai", "open source", "workflow",
    "developer", "orchestration", "llm", "business", "revenue",
}


def _fetch_url(url: str, timeout: float = 20.0) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Source request failed for {url}: {exc}") from exc


def _parse_rss(xml_text: str, source: str, limit: int) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    items: list[dict[str, str]] = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if title and link:
            items.append({
                "source": source, "title": title, "url": link,
                "summary": (item.findtext("description") or "").strip(),
                "published": (item.findtext("pubDate") or "").strip(),
            })
    return items


class _TrendingParser(HTMLParser):
    def __init__(self, limit: int) -> None:
        super().__init__()
        self.limit = limit
        self.in_article = False
        self.in_heading = False
        self.in_repo_link = False
        self.repo_url = ""
        self.title_parts: list[str] = []
        self.items: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "article":
            self.in_article = True
            self.repo_url = ""
            self.title_parts = []
        elif self.in_article and tag == "h2":
            self.in_heading = True
        elif self.in_heading and tag == "a":
            href = attrs_dict.get("href") or ""
            if href.count("/") == 2 and href.startswith("/"):
                self.repo_url = "https://github.com" + href
                self.in_repo_link = True

    def handle_data(self, data: str) -> None:
        if self.in_repo_link:
            self.title_parts.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.in_repo_link:
            self.in_repo_link = False
        elif tag == "h2":
            self.in_heading = False
        elif tag == "article":
            title = " ".join(part for part in self.title_parts if part).strip()
            if self.repo_url and title and len(self.items) < self.limit:
                self.items.append({
                    "source": "GitHub Trending", "title": title,
                    "url": self.repo_url, "summary": "", "published": "",
                })
            self.in_article = False


def fetch_industry_signals(
    sources: dict[str, str] | None = None,
    *,
    limit_per_source: int = 10,
    fetcher=_fetch_url,
) -> dict[str, Any]:
    """Fetch current records and return explicit per-source errors."""
    if limit_per_source < 1:
        raise ValueError("limit_per_source must be at least 1")
    selected = sources or DEFAULT_SOURCES
    signals: list[dict[str, str]] = []
    errors: dict[str, str] = {}
    for source, url in selected.items():
        try:
            body = fetcher(url)
            if source == "GitHub Trending":
                parser = _TrendingParser(limit_per_source)
                parser.feed(body)
                signals.extend(parser.items)
            else:
                signals.extend(_parse_rss(body, source, limit_per_source))
        except (RuntimeError, ET.ParseError, ValueError) as exc:
            errors[source] = str(exc)
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "signals": signals, "source_errors": errors,
        "sources_checked": len(selected),
    }


def analyze_with_rules(raw_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Create transparent rule-based briefs; this is not an LLM analysis."""
    insights: list[dict[str, Any]] = []
    for signal in raw_data.get("signals", []):
        text = f"{signal.get('title', '')} {signal.get('summary', '')}".lower()
        matches = sorted(term for term in HIGH_VALUE_TERMS if term in text)
        if not matches:
            continue
        impact = "High" if len(matches) >= 3 else "Medium" if len(matches) == 2 else "Low"
        insights.append({
            "summary": signal.get("title", "Untitled signal"),
            "impact": impact,
            "action_item": (
                "Review the source and test whether it solves a current ULTRON "
                "operational bottleneck; do not adopt without a working proof."
            ),
            "source": signal.get("source", "Unknown"),
            "url": signal.get("url", ""),
            "matched_terms": matches,
            "analysis_mode": "transparent_keyword_rules",
            "timestamp": raw_data.get("fetched_at", datetime.now(timezone.utc).isoformat()),
        })
    return insights


def publish_report(
    raw_data: dict[str, Any],
    insights: list[dict[str, Any]],
    output_path: str | Path = "market_intelligence_log.md",
) -> Path:
    """Write a Markdown briefing with provenance and collection failures."""
    path = Path(output_path)
    lines = [
        "# ULTRON Market Intelligence", "",
        f"- Collected: {raw_data.get('fetched_at', 'unknown')}",
        f"- Sources checked: {raw_data.get('sources_checked', 0)}",
        f"- Signals collected: {len(raw_data.get('signals', []))}",
        f"- Actionable matches: {len(insights)}",
        "- Analysis: transparent keyword rules (not an LLM assessment)", "",
    ]
    for insight in insights:
        lines.extend([
            f"## {insight['summary']}",
            f"- **Impact heuristic:** {insight['impact']}",
            f"- **Action:** {insight['action_item']}",
            f"- **Source:** {insight['source']}",
            f"- **Evidence:** {insight['url']}",
            f"- **Matched terms:** {', '.join(insight['matched_terms'])}", "",
        ])
    if not insights:
        lines.extend(["No signals matched the current relevance rules.", ""])
    errors = raw_data.get("source_errors", {})
    if errors:
        lines.extend(["## Source errors", ""])
        lines.extend(f"- **{name}:** {message}" for name, message in errors.items())
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
