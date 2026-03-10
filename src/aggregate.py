#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "rich",
# ]
# ///

"""
Deduplicate bonds CSV by ISIN.
Reads bonds.csv, groups by ISIN, and aggregates trading venues into a single record per bond.

Run with: uv run aggregate.py
"""

import csv
from collections import defaultdict
from pathlib import Path

from rich.console import Console

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "bonds.csv"

console = Console()


def aggregate(csv_path: Path = CSV_PATH) -> tuple[list[dict], int]:
    """
    Read CSV, group by ISIN, aggregate venues, return deduped records.

    For each ISIN group:
    - Sort by (valid_from_date, first_trade_date) ascending
    - Empty date strings treated as "9999-99-99" (sort last)
    - Canonical record = first in sorted order
    - Aggregate all trading_venue_mic values (deduped, order-preserved) into tradable_venues_mic
    - Drop id and trading_venue_mic columns

    Returns: tuple of (list[dict] with one entry per unique ISIN, total rows read)
    """
    groups = defaultdict(list)
    total_rows = 0

    # Stream read CSV
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            isin = row["isin"]
            groups[isin].append(row)
            total_rows += 1

    result = []

    for isin in groups:
        group = groups[isin]

        # Sort by (valid_from_date, first_trade_date)
        # Empty strings sort as "9999-99-99" (sort last)
        def sort_key(row):
            vfd = row["valid_from_date"] or "9999-99-99"
            ftd = row["first_trade_date"] or "9999-99-99"
            return (vfd, ftd)

        group.sort(key=sort_key)

        # Canonical record = first in sorted group
        canonical = group[0].copy()

        # Aggregate venues: deduped, order-preserved
        venues = []
        for row in group:
            venue = row["trading_venue_mic"]
            if venue and venue not in venues:
                venues.append(venue)

        # Add aggregated venues, drop id and trading_venue_mic
        canonical["tradable_venues_mic"] = ",".join(venues)
        del canonical["id"]
        del canonical["trading_venue_mic"]

        result.append(canonical)

    return result, total_rows


def main() -> list[dict]:
    """Run aggregation and print stats."""
    records, total_rows = aggregate()

    # Count multi-venue bonds
    multi_venue_count = sum(1 for r in records if "," in r.get("tradable_venues_mic", ""))

    console.rule("[bold]Bonds CSV Aggregation[/bold]")
    console.print(f"Rows read      : [bold]{total_rows:,}[/bold]")
    console.print(f"Unique ISINs   : [bold]{len(records):,}[/bold]")
    console.print(f"Multi-venue    : [bold]{multi_venue_count:,}[/bold]")
    console.rule("[bold green]Done[/bold green]")

    return records


if __name__ == "__main__":
    main()
