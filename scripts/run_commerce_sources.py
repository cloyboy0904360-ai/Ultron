"""Collect evidence from explicitly configured, read-only commerce feeds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ultron.commerce_sources import (
    SourceDefinition,
    collect_sources,
    collection_to_dict,
)


def load_sources(path: str | Path) -> tuple[SourceDefinition, ...]:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("version") != 1:
        raise ValueError("source config must be a version 1 JSON object")
    items = config.get("sources")
    if not isinstance(items, list):
        raise ValueError("source config must contain a sources array")
    return tuple(SourceDefinition(**item) for item in items)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/commerce_sources.json")
    parser.add_argument("--output", default="commerce_source_report.json")
    args = parser.parse_args()

    sources = load_sources(args.config)
    result = collect_sources(sources)
    report = collection_to_dict(result)
    Path(args.output).write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Configured: {result.sources_configured}; "
        f"succeeded: {result.sources_succeeded}; "
        f"records: {len(result.records)}; errors: {len(result.source_errors)}"
    )
    return 0 if not result.source_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
