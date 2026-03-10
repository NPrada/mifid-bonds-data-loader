#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "httpx",
#   "rich",
# ]
# ///

"""
FIRDS Bonds Full Pipeline
Runs the complete data loading pipeline end-to-end:
  1. Download FULINS_D XML files from ESMA
  2. Parse XML files to bonds.csv
  3. Aggregate by ISIN (deduplicate)
  4. Persist to SQLite

Run with: uv run main.py
"""

from rich.console import Console

from src.download_full_reference import main as download
from src.parser import main as parse_to_csv
from src.aggregate import aggregate
from src.persistor import main as persist_records

console = Console()


def main() -> None:
    console.rule("[bold cyan]FIRDS Bonds Full Pipeline[/bold cyan]")

    console.rule("[bold]Step 1 — Downloading[/bold]")
    download()

    console.rule("[bold]Step 2 — Parsing XML to CSV[/bold]")
    parse_to_csv()

    console.rule("[bold]Step 3 — Aggregating by ISIN[/bold]")
    records, _ = aggregate()

    console.rule("[bold]Step 4 — Persisting to SQLite[/bold]")
    persist_records(records)

    console.rule("[bold green]Pipeline complete[/bold green]")


if __name__ == "__main__":
    main()
