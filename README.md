# MIFID Bonds Data Loader

Automated pipeline to download, parse, and deduplicate FIRDS (Financial Instruments Reference Data System) bond data from EU regulatory sources, producing a clean SQLite database of unique bonds with aggregated trading venue information.

## Overview

This tool processes regulatory bond data from ESMA's FIRDS XML feeds:
1. **Download** - Fetches FULINS_D XML files from ESMA's data portal
2. **Parse** - Extracts structured data from XML into a consolidated CSV (1.5M+ records)
3. **Aggregate** - Deduplicates by ISIN, merging venue information (602k unique bonds)
4. **Persist** - Loads deduplicated data into SQLite for analysis

The resulting `bonds.db` SQLite database contains all unique bonds across European trading venues.

## Quick Start

### Prerequisites
- Python 3.12+
- `uv` package manager
- ~1.5GB free disk space (intermediate CSV is ~540MB)

### Installation
```bash
git clone <repo>
cd mifid-bonds-data-loader
source .venv/bin/activate  # or create with: python3 -m venv .venv
```

### Running the Pipeline

**Run the full pipeline** (download → parse → aggregate → persist in one command)
```bash
uv run main.py
```

Each step can also be run independently from the `src/` directory:

## Project Structure

```
.
├── main.py                        # Orchestrator: runs all 4 steps sequentially
├── README.md                      # This file
├── SCHEMA.md                      # SQLite database schema documentation
├── pyproject.toml                 # Project configuration & dependencies
│
├── src/
│   ├── download_full_reference.py # Step 1: Download FULINS_D XMLs from ESMA
│   ├── parser.py                  # Step 2: Parse XML files to bonds.csv
│   ├── aggregate.py               # Step 3: Deduplicate CSV by ISIN
│   └── persistor.py               # Step 4: Persist records to SQLite
│
└── data/
    ├── bonds.csv                  # Intermediate CSV (~540MB, 1.5M rows)
    ├── bonds.db                   # Final SQLite database (~160MB)
    └── FULINS_D_*.zip             # Downloaded XML archives
```

**Pipeline flow**:
```
main.py (orchestrator)
  ├─→ src.download_full_reference  (downloads FULINS_D ZIP files, extracts XMLs)
  ├─→ src.parser                   (parses XMLs → bonds.csv)
  ├─→ src.aggregate                (groups by ISIN, deduplicates, aggregates venues)
  └─→ src.persistor                (creates SQLite table, upserts 602k unique ISINs)
```

## How It Works

### 1. Downloader (`download_full_reference.py`)
- Queries ESMA FIRDS system to find latest available FULINS_D files
- Downloads the weekly full reference data files (FULINS_D_YYYYMMDD_01of04, etc.)
- Extracts ZIP archives to `data/FULINS_D_*/` subdirectories
- Handles retries and skips files already downloaded (idempotent)

### 2. Parser (`parser.py`)
- Reads XML files from `data/FULINS_D_*/` directories
- Streams-parses large XML files to minimize memory footprint (no loading entire file in RAM)
- Extracts 37 fields per bond-venue pair using ISO 20022 element paths
- Outputs: `data/bonds.csv` (1.5M+ rows, one row per ISIN-venue pair)
- Sorts by `id` (composite key) for stable output

**Fields**: ISIN, bond name, CFI classification, interest rate type, maturity date, issuer LEI, trading venue MIC code, and more.

### 3. Aggregator (`aggregate.py`)
- Reads CSV and groups rows by ISIN
- For each ISIN group:
  - Sorts by `(valid_from_date, first_trade_date)` to pick canonical record
  - Aggregates all trading venues into a comma-separated list in `tradable_venues_mic`
  - Drops composite `id` and duplicate `trading_venue_mic` columns
- Returns: ~602k deduped bond records with aggregated venues (in-memory)

**Aggregation stats**:
- Input: 1,515,167 rows (CSV, one per ISIN-venue)
- Unique ISINs: 602,825 (output records)
- Multi-venue bonds: 337,473 (55.6%)

### 4. Persistor (`persistor.py`)
- Accepts deduped bond records from aggregator
- Uses dependency injection pattern: `RecordWriter` callable for flexible storage backends
- Creates SQLite table: 36 columns (all TEXT), ISIN as primary key
- Upserts all records via `INSERT OR REPLACE` (idempotent, safe to re-run)
- Outputs: `data/bonds.db` (602,825 records, ~160MB on disk)

## Database

See [schema.md](./docs/schema.md) for complete schema documentation.