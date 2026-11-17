"""Run ULTRON's public-source market intelligence collector."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# When executed as a script, Python puts scripts/ (not the repository root)
# on sys.path. Add the repository root so the ultron package is importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ultron.market_intelligence import (
    analyze_with_rules,
    fetch_industry_signals,
    publish_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="market_intelligence_log.md")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    raw = fetch_industry_signals(limit_per_source=args.limit)
    insights = analyze_with_rules(raw)
    report = publish_report(raw, insights, args.output)
    print(json.dumps({
        "status": "COMPLETED" if raw["signals"] else "NO_SIGNALS",
        "report": str(report),
        "signals_collected": len(raw["signals"]),
        "actionable_matches": len(insights),
        "source_errors": raw["source_errors"],
    }, indent=2))
    return 0 if raw["signals"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
