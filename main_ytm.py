#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "rich",
#   "yfinance>=0.2",
#   "scipy>=1.13",
# ]
# ///

"""
YTM Pipeline
Fetches bond prices and calculates Yield-to-Maturity for all eligible bonds
in bonds.db, then stores results back into bonds.db.

Pipeline:
  1. Load eligible bonds from bonds.db (fixed-rate + zero-coupon, not matured)
  2. Fetch current prices via Yahoo Finance
  3. Calculate YTM for each bond with a price
  4. Persist prices + YTM to bond_prices / bond_ytm tables in bonds.db

Assumptions baked in:
  - Coupon frequency: annual (most EUR bonds use annual coupons).
    Override DEFAULT_COUPON_FREQ below if your universe is predominantly
    semi-annual (e.g. US/UK bonds).
  - Prices are treated as clean prices (% of par).  Yahoo Finance may return
    dirty prices; this introduces a small error near coupon dates.
  - Day count: actual/365.25.

Run with: uv run main_ytm.py [--limit N]
"""

import argparse
import sqlite3
from pathlib import Path

from rich.console import Console
from rich.table import Table

from src.calculate_ytm import calculate_ytm_fixed, calculate_ytm_zero_coupon
from src.fetch_prices import PriceRecord, fetch_prices_for_db
from src.persist_ytm import ensure_tables, stats, upsert_prices, upsert_ytm

DATA_DIR = Path("data")
SQLITE_PATH = DATA_DIR / "bonds.db"

# Change to 2 if your bonds are predominantly semi-annual (USD/GBP denominated)
DEFAULT_COUPON_FREQ = 1

console = Console()


def run(limit: int | None = None) -> None:
    console.rule("[bold cyan]YTM Pipeline[/bold cyan]")

    if not SQLITE_PATH.exists():
        console.print(f"[red]bonds.db not found at {SQLITE_PATH}. Run main.py first.[/red]")
        return

    # --- Step 1: Fetch prices ---
    console.rule("[bold]Step 1 — Fetching prices (Yahoo Finance)[/bold]")
    price_records: dict[str, PriceRecord] = fetch_prices_for_db(
        db_path=SQLITE_PATH,
        limit=limit,
    )

    if not price_records:
        console.print("[yellow]No prices found. Nothing to calculate.[/yellow]")
        return

    # --- Step 2: Persist prices ---
    console.rule("[bold]Step 2 — Persisting prices[/bold]")
    conn = sqlite3.connect(SQLITE_PATH)
    ensure_tables(conn)

    price_dicts = [
        {
            "isin": rec.isin,
            "price_pct": rec.price_pct,
            "price_date": rec.price_date,
            "source_ticker": rec.source_ticker,
            "source": rec.source,
        }
        for rec in price_records.values()
    ]
    upsert_prices(conn, price_dicts)
    console.print(f"Stored [bold]{len(price_dicts):,}[/bold] price records.")

    # --- Step 3: Load bond attributes for YTM calculation ---
    console.rule("[bold]Step 3 — Calculating YTM[/bold]")
    isins = list(price_records.keys())
    placeholders = ",".join("?" * len(isins))
    bond_rows = conn.execute(
        f"""
        SELECT isin, interest_rate_type, fixed_rate, maturity_date
        FROM bonds
        WHERE isin IN ({placeholders})
        """,
        isins,
    ).fetchall()

    bond_map = {
        row[0]: {
            "interest_rate_type": row[1],
            "fixed_rate": row[2],
            "maturity_date": row[3],
        }
        for row in bond_rows
    }

    ytm_records: list[dict] = []
    skipped_no_maturity = 0
    skipped_calc_error = 0

    for isin, price_rec in price_records.items():
        bond = bond_map.get(isin)
        if not bond:
            continue

        rate_type = bond["interest_rate_type"]
        maturity = bond["maturity_date"]

        if not maturity:
            skipped_no_maturity += 1
            continue

        ytm: float | None = None

        if rate_type == "fixed":
            try:
                coupon = float(bond["fixed_rate"])
            except (TypeError, ValueError):
                skipped_calc_error += 1
                continue
            ytm = calculate_ytm_fixed(
                price_pct=price_rec.price_pct,
                coupon_rate_pct=coupon,
                maturity_date_str=maturity,
                coupon_freq=DEFAULT_COUPON_FREQ,
            )

        elif rate_type == "zero_coupon":
            ytm = calculate_ytm_zero_coupon(
                price_pct=price_rec.price_pct,
                maturity_date_str=maturity,
            )

        if ytm is None:
            skipped_calc_error += 1
            continue

        ytm_records.append({
            "isin": isin,
            "ytm": ytm,
            "price_pct": price_rec.price_pct,
            "price_date": price_rec.price_date,
            "coupon_freq": DEFAULT_COUPON_FREQ,
        })

    # --- Step 4: Persist YTM ---
    upsert_ytm(conn, ytm_records)

    # --- Summary ---
    s = stats(conn)
    conn.close()

    console.rule("[bold green]Done[/bold green]")

    table = Table(title="YTM Pipeline Results", show_lines=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Total bonds in DB", f"{s['total_bonds']:,}")
    table.add_row("Bonds with a price", f"{s['priced']:,}")
    table.add_row("Bonds with YTM calculated", f"{s['with_ytm']:,}")
    table.add_row("Skipped (no maturity date)", f"{skipped_no_maturity:,}")
    table.add_row("Skipped (calc error / bad data)", f"{skipped_calc_error:,}")
    console.print(table)

    if ytm_records:
        console.print("\n[bold]Sample YTMs:[/bold]")
        for rec in ytm_records[:10]:
            console.print(
                f"  {rec['isin']}  price={rec['price_pct']:.2f}%  "
                f"YTM={rec['ytm']*100:.3f}%  ({rec['price_date']})"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch bond prices and calculate YTM")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N eligible bonds (useful for testing)",
    )
    args = parser.parse_args()
    run(limit=args.limit)


if __name__ == "__main__":
    main()
