#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "rich",
#   "QuantLib",
# ]
# ///

"""
Compute Yield to Maturity (YTM) for bonds with prices.

Reads from the `prices` table, joins to the `bonds` table, and computes YTM
for fixed-rate bonds using QuantLib (industry-standard fixed-income library).

Day count conventions are configurable; default is ActualActual.ISMA, the
ICMA standard for European bonds.

Run with: uv run src/ytm.py
"""

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import QuantLib as ql
from rich.console import Console

DATA_DIR = Path("data")
SQLITE_PATH = DATA_DIR / "bonds.db"
BONDS_TABLE = "bonds"
PRICES_TABLE = "prices"

console = Console()

# ---------------------------------------------------------------------------
# Day count conventions: string name -> QuantLib day counter
# ---------------------------------------------------------------------------

DAY_COUNTERS: dict[str, ql.DayCounter] = {
    "ActualActual.ISMA":   ql.ActualActual(ql.ActualActual.ISMA),
    "ActualActual.Bond":   ql.ActualActual(ql.ActualActual.Bond),
    "ActualActual.ISDA":   ql.ActualActual(ql.ActualActual.ISDA),
    "Thirty360.BondBasis": ql.Thirty360(ql.Thirty360.BondBasis),
    "Thirty360.European":  ql.Thirty360(ql.Thirty360.European),
    "Actual360":           ql.Actual360(),
    "Actual365Fixed":      ql.Actual365Fixed(),
}

FREQUENCIES: dict[str, int] = {
    "Annual":     ql.Annual,
    "Semiannual": ql.Semiannual,
    "Quarterly":  ql.Quarterly,
    "Monthly":    ql.Monthly,
}

DEFAULT_DAY_COUNT = "ActualActual.ISMA"
DEFAULT_FREQUENCY = "Annual"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def ensure_prices_table(conn: sqlite3.Connection) -> None:
    """Create the prices table if it does not exist."""
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {PRICES_TABLE} (
            isin TEXT NOT NULL,
            price_date TEXT NOT NULL,
            clean_price TEXT NOT NULL,
            source TEXT DEFAULT '',
            ytm TEXT DEFAULT '',
            ytm_day_count TEXT DEFAULT '',
            computed_at TEXT DEFAULT '',
            PRIMARY KEY (isin, price_date),
            FOREIGN KEY (isin) REFERENCES {BONDS_TABLE}(isin)
        )
        """
    )
    conn.commit()


def insert_prices(db_path: Path, prices: list[dict]) -> int:
    """
    Insert price records into the prices table.

    Each dict should have: isin, price_date (YYYY-MM-DD), clean_price (str),
    and optionally source.

    Uses INSERT OR REPLACE so re-inserting the same (isin, price_date) updates
    the row and clears any previously computed YTM.
    """
    conn = sqlite3.connect(db_path)
    ensure_prices_table(conn)
    cursor = conn.cursor()

    sql = f"""
        INSERT OR REPLACE INTO {PRICES_TABLE}
            (isin, price_date, clean_price, source, ytm, ytm_day_count, computed_at)
        VALUES (?, ?, ?, ?, '', '', '')
    """
    rows = [
        (
            p["isin"],
            p["price_date"],
            str(p["clean_price"]),
            p.get("source", ""),
        )
        for p in prices
    ]
    cursor.executemany(sql, rows)
    conn.commit()
    conn.close()
    return len(rows)


# ---------------------------------------------------------------------------
# YTM computation
# ---------------------------------------------------------------------------

def _to_ql_date(d: date) -> ql.Date:
    return ql.Date(d.day, d.month, d.year)


def compute_ytm(
    fixed_rate: float,
    nominal_value: float,
    clean_price_pct: float,
    maturity_date: date,
    settlement_date: date,
    frequency: str = DEFAULT_FREQUENCY,
    day_count: str = DEFAULT_DAY_COUNT,
) -> float | None:
    """
    Compute YTM for a fixed-rate bond.

    Args:
        fixed_rate: Annual coupon rate as a percentage (e.g. 2.5 means 2.5%).
        nominal_value: Face/par value per unit (e.g. 1000).
        clean_price_pct: Clean price as a percentage of par (e.g. 98.5).
        maturity_date: Bond maturity date.
        settlement_date: Date the price applies to (used as settlement).
        frequency: Coupon frequency name. See FREQUENCIES dict.
        day_count: Day count convention name. See DAY_COUNTERS dict.

    Returns:
        YTM as an annualized percentage (e.g. 3.45 for 3.45%), or None if
        the inputs are invalid or the solver fails to converge.
    """
    if maturity_date <= settlement_date:
        return None
    if clean_price_pct <= 0 or nominal_value <= 0:
        return None

    day_counter = DAY_COUNTERS[day_count]
    ql_freq = FREQUENCIES[frequency]

    ql_settlement = _to_ql_date(settlement_date)
    ql_maturity = _to_ql_date(maturity_date)

    ql.Settings.instance().evaluationDate = ql_settlement

    calendar = ql.NullCalendar()
    schedule = ql.Schedule(
        ql_settlement,
        ql_maturity,
        ql.Period(ql_freq),
        calendar,
        ql.Unadjusted,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )

    try:
        bond = ql.FixedRateBond(
            0,                       # settlement days
            nominal_value,           # face amount
            schedule,
            [fixed_rate / 100.0],    # coupon as decimal
            day_counter,
        )
        bond_price = ql.BondPrice(clean_price_pct, ql.BondPrice.Clean)
        ytm = bond.bondYield(
            bond_price,
            day_counter,
            ql.Compounded,
            ql_freq,
            ql_settlement,
        )
    except RuntimeError:
        return None

    return ytm * 100.0


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _parse_date(s: str) -> date | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def process_ytm(
    db_path: Path = SQLITE_PATH,
    day_count: str = DEFAULT_DAY_COUNT,
    frequency: str = DEFAULT_FREQUENCY,
) -> tuple[int, int, int]:
    """
    Compute YTM for all eligible price rows.

    Eligible = fixed-rate bond + price exists + ytm not yet computed.

    Returns: (eligible, computed, skipped)
    """
    conn = sqlite3.connect(db_path)
    ensure_prices_table(conn)
    cursor = conn.cursor()

    select_sql = f"""
        SELECT p.isin, p.price_date, p.clean_price,
               b.fixed_rate, b.nominal_value_per_unit, b.maturity_date
        FROM {PRICES_TABLE} p
        JOIN {BONDS_TABLE} b ON p.isin = b.isin
        WHERE b.interest_rate_type = 'fixed'
          AND p.ytm = ''
          AND p.clean_price != ''
          AND b.fixed_rate != ''
          AND b.maturity_date != ''
          AND b.nominal_value_per_unit != ''
    """
    rows = cursor.execute(select_sql).fetchall()

    update_sql = f"""
        UPDATE {PRICES_TABLE}
        SET ytm = ?, ytm_day_count = ?, computed_at = ?
        WHERE isin = ? AND price_date = ?
    """

    eligible = len(rows)
    computed = 0
    skipped = 0

    for isin, price_date_str, clean_price_str, fixed_rate_str, nominal_str, maturity_str in rows:
        settlement_date = _parse_date(price_date_str)
        maturity_date = _parse_date(maturity_str)
        try:
            fixed_rate = float(fixed_rate_str)
            nominal_value = float(nominal_str)
            clean_price = float(clean_price_str)
        except ValueError:
            skipped += 1
            continue

        if settlement_date is None or maturity_date is None:
            skipped += 1
            continue

        ytm = compute_ytm(
            fixed_rate=fixed_rate,
            nominal_value=nominal_value,
            clean_price_pct=clean_price,
            maturity_date=maturity_date,
            settlement_date=settlement_date,
            frequency=frequency,
            day_count=day_count,
        )

        if ytm is None:
            skipped += 1
            continue

        cursor.execute(
            update_sql,
            (
                f"{ytm:.4f}",
                day_count,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                isin,
                price_date_str,
            ),
        )
        computed += 1

    conn.commit()
    conn.close()
    return eligible, computed, skipped


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    console.rule("[bold]Bond YTM Computation[/bold]")
    console.print(f"Database         : [cyan]{SQLITE_PATH}[/cyan]")
    console.print(f"Day count        : [cyan]{DEFAULT_DAY_COUNT}[/cyan]")
    console.print(f"Coupon frequency : [cyan]{DEFAULT_FREQUENCY}[/cyan]\n")

    eligible, computed, skipped = process_ytm(SQLITE_PATH)

    console.print(f"Eligible rows  : [bold]{eligible:,}[/bold]")
    console.print(f"Computed       : [bold green]{computed:,}[/bold green]")
    console.print(f"Skipped        : [bold yellow]{skipped:,}[/bold yellow]")
    console.rule("[bold green]Done[/bold green]")


if __name__ == "__main__":
    main()
