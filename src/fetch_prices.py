#!/usr/bin/env python3
"""
Bond price fetcher — Yahoo Finance source.

Fetches the most recent closing price for each bond ISIN by trying Yahoo Finance
tickers constructed from the ISIN + exchange suffix derived from the bond's
tradable venues (stored in bonds.db).

Coverage: ~10k–30k liquid EU bonds (large corporates, government bonds listed on
major exchanges). Illiquid/OTC bonds will return no price.

NOTE on ESMA FITRS (post-trade transparency data)
--------------------------------------------------
ESMA publishes MiFID II post-trade transaction data through the FITRS system,
which is separate from the FIRDS reference data system used in this repo.
The FITRS endpoint is expected to be at:
  https://registers.esma.europa.eu/solr/esma_registers_fitrs_files/select
with file naming like FULPRI_D_YYYYMMDD_XXofXX.zip.
However, this endpoint returns 403 from cloud environments (same IP restriction
as the FIRDS endpoint). Once verified, a FITRS downloader following the same
pattern as src/download_full_reference.py can be added as a second price source.
That would dramatically increase coverage (potentially 50k–200k bonds that
actively traded in the reference period).

Run with: uv run fetch_prices.py  (fetches a sample and prints results)
"""

import sqlite3
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yfinance as yf
from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, Progress, TextColumn, TimeRemainingColumn

DATA_DIR = Path("data")
SQLITE_PATH = DATA_DIR / "bonds.db"

console = Console()

# Yahoo Finance exchange suffix by primary venue MIC
MIC_TO_YF_SUFFIX: dict[str, str] = {
    "XFRA": ".F",    # Frankfurt Stock Exchange (floor)
    "XETR": ".DE",   # XETRA (Deutsche Börse electronic)
    "XPAR": ".PA",   # Euronext Paris
    "XAMS": ".AS",   # Euronext Amsterdam
    "XBRU": ".BR",   # Euronext Brussels
    "XLIS": ".LS",   # Euronext Lisbon
    "XLON": ".L",    # London Stock Exchange
    "XMIL": ".MI",   # Borsa Italiana (Milan)
    "BMEX": ".MC",   # Bolsa de Madrid
    "XHEL": ".HE",   # Nasdaq Helsinki
    "XSTO": ".ST",   # Nasdaq Stockholm
    "XCSE": ".CO",   # Nasdaq Copenhagen
    "XOSL": ".OL",   # Oslo Børs
    "XWAR": ".WA",   # Warsaw Stock Exchange
    "XSWX": ".SW",   # SIX Swiss Exchange
    "XVIE": ".VI",   # Vienna Stock Exchange
    "XDUB": ".IR",   # Euronext Dublin
}

# Throttle: wait this many seconds between individual ticker fetches
# to avoid rate limiting.  Batch download uses a higher limit.
_SINGLE_FETCH_DELAY = 0.3
_BATCH_SIZE = 50     # tickers per yfinance.download() call


@dataclass
class PriceRecord:
    isin: str
    price_pct: float          # price as % of par (e.g. 98.5)
    price_date: str           # ISO date of the price
    source_ticker: str        # the Yahoo Finance ticker used
    source: str = "yahoo_finance"


def _venues_for_isin(conn: sqlite3.Connection, isin: str) -> list[str]:
    row = conn.execute(
        "SELECT tradable_venues_mic FROM bonds WHERE isin = ?", (isin,)
    ).fetchone()
    if not row or not row[0]:
        return []
    return [v.strip() for v in row[0].split(",") if v.strip()]


def _suffixes_for_venues(venues: list[str]) -> list[str]:
    """Return deduplicated Yahoo Finance suffixes for a bond's venues, most likely first."""
    seen: set[str] = set()
    result: list[str] = []
    for mic in venues:
        suffix = MIC_TO_YF_SUFFIX.get(mic)
        if suffix and suffix not in seen:
            seen.add(suffix)
            result.append(suffix)
    return result


def fetch_price_single(isin: str, venues: list[str]) -> PriceRecord | None:
    """
    Try each exchange suffix for an ISIN in order. Returns the first valid price found.
    Uses a short delay per attempt to avoid rate limiting.
    """
    for suffix in _suffixes_for_venues(venues):
        ticker_str = f"{isin}{suffix}"
        try:
            ticker = yf.Ticker(ticker_str)
            hist = ticker.history(period="5d", auto_adjust=False)
            if hist.empty:
                time.sleep(_SINGLE_FETCH_DELAY)
                continue
            price = float(hist["Close"].iloc[-1])
            price_date = hist.index[-1].date().isoformat()
            if price > 0:
                return PriceRecord(
                    isin=isin,
                    price_pct=price,
                    price_date=price_date,
                    source_ticker=ticker_str,
                )
        except Exception:
            pass
        time.sleep(_SINGLE_FETCH_DELAY)
    return None


def fetch_prices_batch(
    isin_venues: list[tuple[str, list[str]]],
) -> dict[str, PriceRecord]:
    """
    Batch-download prices for multiple ISINs using yfinance.download().
    Groups by exchange suffix to minimise API calls.

    Args:
        isin_venues: list of (isin, [venue_mic, ...]) tuples.

    Returns:
        dict mapping ISIN -> PriceRecord for bonds where a price was found.
    """
    # Build: suffix -> [(isin, ticker_str), ...]
    suffix_map: dict[str, list[tuple[str, str]]] = {}
    for isin, venues in isin_venues:
        for suffix in _suffixes_for_venues(venues):
            ticker_str = f"{isin}{suffix}"
            suffix_map.setdefault(suffix, []).append((isin, ticker_str))
            break  # try only the first (most likely) suffix in batch mode

    results: dict[str, PriceRecord] = {}

    for suffix, pairs in suffix_map.items():
        for batch_start in range(0, len(pairs), _BATCH_SIZE):
            batch = pairs[batch_start : batch_start + _BATCH_SIZE]
            tickers = [t for _, t in batch]
            try:
                data = yf.download(
                    tickers,
                    period="5d",
                    auto_adjust=False,
                    progress=False,
                    threads=True,
                )
                if data.empty:
                    continue

                close = data["Close"] if "Close" in data else data.get("Adj Close")
                if close is None:
                    continue

                for isin, ticker_str in batch:
                    if isin in results:
                        continue
                    try:
                        series = close[ticker_str] if ticker_str in close.columns else close
                        last_valid = series.dropna()
                        if last_valid.empty:
                            continue
                        price = float(last_valid.iloc[-1])
                        price_date = last_valid.index[-1].date().isoformat()
                        if price > 0:
                            results[isin] = PriceRecord(
                                isin=isin,
                                price_pct=price,
                                price_date=price_date,
                                source_ticker=ticker_str,
                            )
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(0.5)

    return results


def fetch_prices_for_db(
    db_path: Path = SQLITE_PATH,
    limit: int | None = None,
    rate_types: tuple[str, ...] = ("fixed", "zero_coupon"),
) -> dict[str, PriceRecord]:
    """
    Fetch prices for all (or up to `limit`) YTM-eligible bonds in bonds.db.

    Filters to bonds where:
    - interest_rate_type is in rate_types (default: fixed or zero_coupon)
    - maturity_date is in the future
    - tradable_venues_mic is not empty

    Returns dict of ISIN -> PriceRecord.
    """
    conn = sqlite3.connect(db_path)
    today = date.today().isoformat()

    placeholders = ",".join("?" * len(rate_types))
    query = f"""
        SELECT isin, tradable_venues_mic
        FROM bonds
        WHERE interest_rate_type IN ({placeholders})
          AND maturity_date > ?
          AND tradable_venues_mic IS NOT NULL
          AND tradable_venues_mic != ''
        ORDER BY isin
    """
    if limit:
        query += f" LIMIT {limit}"

    rows = conn.execute(query, (*rate_types, today)).fetchall()
    conn.close()

    isin_venues = [
        (isin, [v.strip() for v in venues.split(",") if v.strip()])
        for isin, venues in rows
    ]

    console.print(f"[bold]Fetching prices for {len(isin_venues):,} bonds via Yahoo Finance...[/bold]")

    results: dict[str, PriceRecord] = {}
    found = 0

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching", total=len(isin_venues))

        for batch_start in range(0, len(isin_venues), _BATCH_SIZE):
            batch = isin_venues[batch_start : batch_start + _BATCH_SIZE]
            batch_results = fetch_prices_batch(batch)
            results.update(batch_results)
            found += len(batch_results)
            progress.advance(task, len(batch))

    hit_rate = 100 * found / len(isin_venues) if isin_venues else 0
    console.print(f"Found prices: [bold green]{found:,}[/bold green] / {len(isin_venues):,} ({hit_rate:.1f}% hit rate)")
    return results


if __name__ == "__main__":
    console.rule("[bold]Bond Price Fetcher — sample run (first 20 eligible bonds)[/bold]")
    prices = fetch_prices_for_db(limit=20)
    if prices:
        console.print("\n[bold]Prices found:[/bold]")
        for isin, rec in prices.items():
            console.print(f"  {isin}  {rec.price_pct:7.3f}%  {rec.price_date}  via {rec.source_ticker}")
    else:
        console.print("[yellow]No prices found in sample — try a different limit or check venue coverage.[/yellow]")
