#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "rich",
# ]
# ///

"""
Persist aggregated bonds records to SQLite.
Dependency injection pattern for flexible storage backends.

Run with: uv run persistor.py
"""

import sqlite3
from pathlib import Path
from typing import Callable

from rich.console import Console

DATA_DIR = Path("data")
SQLITE_PATH = DATA_DIR / "bonds.db"
TABLE_NAME = "bonds"

console = Console()

# Type alias for record writer (dependency injection)
RecordWriter = Callable[[list[dict]], None]

# Column order: all columns except id and trading_venue_mic, with tradable_venues_mic first
COLUMNS = [
    "isin",
    "tradable_venues_mic",
    "full_name",
    "short_name",
    "cfi_code",
    "cfi_debt_type",
    "cfi_interest_type",
    "cfi_guarantee",
    "cfi_redemption",
    "cfi_form",
    "notional_currency",
    "commodity_derivative",
    "issuer_lei",
    "issuer_request",
    "admission_approval_date",
    "request_for_admission_date",
    "first_trade_date",
    "termination_date",
    "total_issued_nominal_amount",
    "total_issued_nominal_currency",
    "maturity_date",
    "nominal_value_per_unit",
    "nominal_value_currency",
    "interest_rate_type",
    "fixed_rate",
    "floating_ref_rate_isin",
    "floating_ref_rate_term_value",
    "floating_ref_rate_term_unit",
    "floating_spread_bps",
    "debt_seniority",
    "debt_seniority_label",
    "underlying_isin",
    "relevant_competent_authority",
    "valid_from_date",
    "relevant_trading_venue",
    "source_file",
]


def make_sqlite_writer(db_path: Path) -> RecordWriter:
    """
    Factory function that returns a closure for writing records to SQLite.

    The returned closure:
    - Opens connection to db_path
    - Creates table if not exists (isin as primary key, all columns TEXT)
    - Upserts records via INSERT OR REPLACE
    - Commits and closes
    """

    def write_records(records: list[dict]) -> None:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table
        col_defs = ", ".join(f'"{col}" TEXT' for col in COLUMNS)
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                "isin" TEXT PRIMARY KEY,
                {", ".join(f'"{col}" TEXT' for col in COLUMNS[1:])}
            )
        """
        cursor.execute(create_sql)

        # Upsert records
        placeholders = ", ".join("?" * len(COLUMNS))
        upsert_sql = f"""
            INSERT OR REPLACE INTO {TABLE_NAME} ({", ".join(f'"{col}"' for col in COLUMNS)})
            VALUES ({placeholders})
        """

        for record in records:
            values = [record.get(col, "") for col in COLUMNS]
            cursor.execute(upsert_sql, values)

        conn.commit()
        conn.close()

    return write_records


def main(records: list[dict], write_records: RecordWriter | None = None) -> None:
    """
    Persist records to storage backend.

    Args:
        records: List of bond record dicts
        write_records: Optional RecordWriter callable. Defaults to SQLite writer.
    """
    if write_records is None:
        write_records = make_sqlite_writer(SQLITE_PATH)

    write_records(records)

    console.rule("[bold]Bonds SQLite Persistence[/bold]")
    console.print(f"Records written : [bold]{len(records):,}[/bold]")
    console.print(f"Output path     : [cyan]{SQLITE_PATH}[/cyan]")
    console.rule("[bold green]Done[/bold green]")


if __name__ == "__main__":
    # For standalone testing: read from aggregate.py
    from aggregate import aggregate

    records, _ = aggregate()
    main(records)
