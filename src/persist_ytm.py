#!/usr/bin/env python3
"""
Persist bond prices and YTM calculations to SQLite.

Adds two tables to bonds.db:

  bond_prices
  -----------
  isin          TEXT PRIMARY KEY
  price_pct     REAL    -- clean price as % of par
  price_date    TEXT    -- ISO date of the price
  source_ticker TEXT    -- Yahoo Finance ticker used
  source        TEXT    -- "yahoo_finance" | "esma_fitrs" | ...
  fetched_at    TEXT    -- ISO datetime of when we fetched it

  bond_ytm
  --------
  isin          TEXT PRIMARY KEY (FK → bonds.isin)
  ytm           REAL    -- annualized YTM as decimal (0.025 = 2.5%)
  ytm_pct       REAL    -- annualized YTM as percentage (2.5)
  price_pct     REAL    -- price used for the calculation
  price_date    TEXT    -- price observation date
  coupon_freq   INTEGER -- 1 = annual, 2 = semi-annual (assumption used)
  calculated_at TEXT    -- ISO datetime of calculation
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path("data")
SQLITE_PATH = DATA_DIR / "bonds.db"


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bond_prices (
            isin          TEXT PRIMARY KEY,
            price_pct     REAL NOT NULL,
            price_date    TEXT NOT NULL,
            source_ticker TEXT,
            source        TEXT,
            fetched_at    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS bond_ytm (
            isin          TEXT PRIMARY KEY,
            ytm           REAL,
            ytm_pct       REAL,
            price_pct     REAL,
            price_date    TEXT,
            coupon_freq   INTEGER,
            calculated_at TEXT NOT NULL
        );
    """)
    conn.commit()


def upsert_prices(conn: sqlite3.Connection, prices: list[dict]) -> None:
    """
    Args:
        prices: list of dicts with keys: isin, price_pct, price_date,
                source_ticker, source
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """
        INSERT OR REPLACE INTO bond_prices
            (isin, price_pct, price_date, source_ticker, source, fetched_at)
        VALUES (:isin, :price_pct, :price_date, :source_ticker, :source, :fetched_at)
        """,
        [{**p, "fetched_at": now} for p in prices],
    )
    conn.commit()


def upsert_ytm(conn: sqlite3.Connection, ytm_records: list[dict]) -> None:
    """
    Args:
        ytm_records: list of dicts with keys: isin, ytm, price_pct,
                     price_date, coupon_freq
    """
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """
        INSERT OR REPLACE INTO bond_ytm
            (isin, ytm, ytm_pct, price_pct, price_date, coupon_freq, calculated_at)
        VALUES (:isin, :ytm, :ytm_pct, :price_pct, :price_date, :coupon_freq, :calculated_at)
        """,
        [
            {
                **r,
                "ytm_pct": round(r["ytm"] * 100, 6) if r["ytm"] is not None else None,
                "calculated_at": now,
            }
            for r in ytm_records
        ],
    )
    conn.commit()


def load_prices(conn: sqlite3.Connection) -> dict[str, dict]:
    """Return all stored prices as {isin: {price_pct, price_date, ...}}."""
    rows = conn.execute(
        "SELECT isin, price_pct, price_date, source_ticker, source FROM bond_prices"
    ).fetchall()
    return {
        row[0]: {
            "price_pct": row[1],
            "price_date": row[2],
            "source_ticker": row[3],
            "source": row[4],
        }
        for row in rows
    }


def stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM bonds").fetchone()[0]
    priced = conn.execute("SELECT COUNT(*) FROM bond_prices").fetchone()[0]
    with_ytm = conn.execute(
        "SELECT COUNT(*) FROM bond_ytm WHERE ytm IS NOT NULL"
    ).fetchone()[0]
    return {"total_bonds": total, "priced": priced, "with_ytm": with_ytm}
