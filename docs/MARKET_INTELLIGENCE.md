# ULTRON Market Intelligence Agent

## Purpose

Collect public technology signals from Hacker News RSS and GitHub Trending,
retain source URLs, apply transparent relevance rules, and publish a Markdown
briefing. This is an evidence-gathering workflow, not an automated purchasing,
deployment, or trading agent.

## Run locally

```bash
python scripts/run_market_intelligence.py
```

Optional arguments:

```bash
python scripts/run_market_intelligence.py --limit 15 --output reports/market-intelligence.md
```

The collector uses Python's standard library; no paid API, API key, or additional
package is required. Each source failure is recorded separately. A run with no
signals exits non-zero so automation can flag the failure rather than report a
false success.

## Analysis limits

The initial analyzer uses a small, inspectable keyword rule set. It is not an
LLM and its High/Medium/Low impact labels are heuristic triage, not verified
business impact. Every proposed action must be checked against its source.
An LLM provider can be added later behind an explicitly configured credential
and cost approval; this workflow does not call a paid model API.

## Automation

The GitHub Actions workflow can be run manually or on its daily schedule. It
uploads the generated Markdown report as a workflow artifact. It does not
commit reports, contact customers, change connected accounts, spend money, or
publish externally.
