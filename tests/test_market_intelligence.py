from __future__ import annotations

from pathlib import Path

from ultron.market_intelligence import (
    _TrendingParser,
    _parse_rss,
    analyze_with_rules,
    fetch_industry_signals,
    publish_report,
)


def test_parse_rss_extracts_real_item_fields():
    xml = """<rss><channel><item><title>Open source AI agent workflow</title>
    <link>https://example.com/story</link><description>Build automation</description>
    <pubDate>Tue, 17 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>"""
    rows = _parse_rss(xml, "Hacker News", 5)
    assert rows[0]["title"] == "Open source AI agent workflow"
    assert rows[0]["url"] == "https://example.com/story"
    assert rows[0]["source"] == "Hacker News"


def test_github_trending_parser_extracts_repository_links():
    html = """<article><h2><a href="/octo/project">octo / project</a></h2></article>"""
    parser = _TrendingParser(5)
    parser.feed(html)
    assert parser.items == [{
        "source": "GitHub Trending",
        "title": "octo / project",
        "url": "https://github.com/octo/project",
        "summary": "",
        "published": "",
    }]


def test_fetch_collects_success_and_reports_source_errors():
    def fake_fetch(url: str) -> str:
        if "bad" in url:
            raise RuntimeError("offline")
        return (
            "<rss><channel><item><title>AI automation</title>"
            "<link>https://e.test</link></item></channel></rss>"
        )

    result = fetch_industry_signals(
        {"Hacker News": "https://good", "Other": "https://bad"},
        fetcher=fake_fetch,
    )
    assert len(result["signals"]) == 1
    assert result["signals"][0]["source"] == "Hacker News"
    assert result["source_errors"] == {"Other": "offline"}


def test_analysis_is_explicitly_rule_based():
    data = {
        "fetched_at": "2026-11-17T00:00:00+00:00",
        "signals": [{
            "source": "Hacker News",
            "title": "Open source AI agent automation workflow",
            "url": "https://example.com",
        }],
    }
    insights = analyze_with_rules(data)
    assert insights[0]["impact"] == "High"
    assert insights[0]["analysis_mode"] == "transparent_keyword_rules"
    assert insights[0]["url"] == "https://example.com"


def test_publish_report_records_evidence_and_source_errors(tmp_path: Path):
    raw = {
        "fetched_at": "2026-11-17T00:00:00+00:00",
        "sources_checked": 1,
        "signals": [],
        "source_errors": {"Hacker News": "offline"},
    }
    path = publish_report(raw, [], tmp_path / "brief.md")
    report = path.read_text(encoding="utf-8")
    assert "No signals matched" in report
    assert "Hacker News" in report
    assert "offline" in report
