"""Generate the offline ULTRON revenue-opportunity ranking report."""
from __future__ import annotations

import argparse

from ultron.revenue_opportunities import write_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="reports/revenue-opportunities.md",
        help="Markdown report destination (default: reports/revenue-opportunities.md)",
    )
    args = parser.parse_args()
    report = write_report(args.output)
    print(f"Report generated: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
