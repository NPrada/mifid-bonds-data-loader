# SQLite Database Schema: bonds.db

## Overview

The `bonds.db` SQLite database is the deduplicated output of the MIFID bonds data pipeline. It contains one table: `bonds`, with 602,825 rows (one per unique ISIN).

**Key difference from CSV**: The CSV has one row per **(ISIN, trading venue)** combination (~1.5M rows). The SQLite database has one row per **unique ISIN**, with all trading venues aggregated into a comma-separated list in the `tradable_venues_mic` column.

| Metric | Value |
|--------|-------|
| Table name | `bonds` |
| Total records | 602,825 |
| Primary key | `isin` |
| Columns | 36 (all TEXT type) |
| Database size | ~160MB |
| Multi-venue bonds | 337,473 (55.6%) |

---

## Schema Definition

```sql
CREATE TABLE bonds (
    isin TEXT PRIMARY KEY,
    tradable_venues_mic TEXT,
    full_name TEXT,
    short_name TEXT,
    cfi_code TEXT,
    cfi_debt_type TEXT,
    cfi_interest_type TEXT,
    cfi_guarantee TEXT,
    cfi_redemption TEXT,
    cfi_form TEXT,
    notional_currency TEXT,
    commodity_derivative TEXT,
    issuer_lei TEXT,
    issuer_request TEXT,
    admission_approval_date TEXT,
    request_for_admission_date TEXT,
    first_trade_date TEXT,
    termination_date TEXT,
    total_issued_nominal_amount TEXT,
    total_issued_nominal_currency TEXT,
    maturity_date TEXT,
    nominal_value_per_unit TEXT,
    nominal_value_currency TEXT,
    interest_rate_type TEXT,
    fixed_rate TEXT,
    floating_ref_rate_isin TEXT,
    floating_ref_rate_term_value TEXT,
    floating_ref_rate_term_unit TEXT,
    floating_spread_bps TEXT,
    debt_seniority TEXT,
    debt_seniority_label TEXT,
    underlying_isin TEXT,
    relevant_competent_authority TEXT,
    valid_from_date TEXT,
    relevant_trading_venue TEXT,
    source_file TEXT
);
```

---

## Column Reference

### Primary Key

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `isin` | TEXT (PRIMARY KEY) | International Securities Identification Number — unique 12-character identifier per bond (ISO 6166) | `XS0123456789` |

---

### Trading Venue Information

| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `tradable_venues_mic` | TEXT | **AGGREGATED**: Comma-separated list of Market Identifier Codes (MIC, ISO 10383) where this bond trades. Deduped and order-preserved from all rows with this ISIN. | `XETR,XEAM,XHEL` | New column created during aggregation. Not in original CSV. |
| `relevant_trading_venue` | TEXT | Primary/relevant trading venue MIC from the canonical record | `XETR` | Derived from the record with earliest `valid_from_date`, then `first_trade_date` |

---

### Bond Identity

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `full_name` | TEXT | Full legal name of the bond (up to 350 chars) | `German Government Bond Bund 2.5% January 2027` |
| `short_name` | TEXT | Short name/code (up to 35 chars) | `BUND 2027` |

---

### Classification (CFI — ISO 10962:2019)

The CFI (Classification of Financial Instruments) code is a 6-character standard. Position 1 is always 'D' (Debt); positions 2-6 are decoded into human-readable columns.

| Column | Type | CFI Position | Description | Values |
|--------|------|---------|-------------|--------|
| `cfi_code` | TEXT | — | Raw 6-character CFI code | `DBFNFR` |
| `cfi_debt_type` | TEXT | 2 | Type of debt | `Bonds`, `Convertible bonds`, `Bonds with warrants`, `MTN`, `Others`, `Mortgage-backed securities`, `Asset-backed securities`, `Municipal bonds`, `Covered bonds`, `Depositary receipts on debt` |
| `cfi_interest_type` | TEXT | 3 | Interest/coupon type | `Fixed rate`, `Variable/floating rate`, `Zero coupon`, `Adjustable/other rate`, `Not applicable` |
| `cfi_guarantee` | TEXT | 4 | Credit guarantee | `Government guaranteed`, `Joint guaranteed`, `Third-party guaranteed`, `Not guaranteed` |
| `cfi_redemption` | TEXT | 5 | Redemption/repayment mechanism | `At maturity (bullet)`, `Callable`, `Puttable`, `Extendible`, `Fixed periodic redemption`, `Other`, `Redeemable at choice` |
| `cfi_form` | TEXT | 6 | Form of issuance | `Bearer`, `Registered`, `Bearer and Registered`, `Nominee/other` |

---

### Notional Currency & Amounts

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `notional_currency` | TEXT | Notional/settlement currency (ISO 4217 code) | `EUR`, `USD`, `GBP` |
| `total_issued_nominal_amount` | TEXT | Total nominal value of all bonds issued | `1000000000` |
| `total_issued_nominal_currency` | TEXT | Currency of total issued amount (ISO 4217) | `EUR` |
| `nominal_value_per_unit` | TEXT | Par value per single bond/unit | `1000` |
| `nominal_value_currency` | TEXT | Currency of nominal per unit (ISO 4217) | `EUR` |

---

### Interest Rate Details

| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `interest_rate_type` | TEXT | Type of interest rate structure | `fixed`, `floating`, or empty | Derived from presence of fixed/floating rates in source |
| `fixed_rate` | TEXT | Fixed annual coupon rate as percentage | `2.5`, `3.125`, `0.0` | Only populated if `interest_rate_type='fixed'` |
| `floating_ref_rate_isin` | TEXT | Reference rate ISIN (e.g., Euribor index) | `EU0009652783` | Only populated if `interest_rate_type='floating'` |
| `floating_ref_rate_term_value` | TEXT | Tenor value of reference rate | `3`, `6`, `12` | Only populated if floating |
| `floating_ref_rate_term_unit` | TEXT | Tenor unit: M=month, W=week, D=day, Y=year | `M`, `W`, `D`, `Y` | Only populated if floating |
| `floating_spread_bps` | TEXT | Spread over reference rate in basis points | `25`, `50`, `120` | Only populated if floating; "120" means +1.20% |

---

### Debt Seniority

| Column | Type | Description | Values |
|--------|------|-------------|--------|
| `debt_seniority` | TEXT | Seniority code (raw) | `SNDB` (senior), `SBOD` (subordinated), `JUND` (junior), or empty |
| `debt_seniority_label` | TEXT | Human-readable seniority | `Senior debt`, `Subordinated debt`, `Junior debt`, or empty |

---

### Structured Products & Derivatives

| Column | Type | Description | Example | Notes |
|--------|------|-------------|---------|-------|
| `underlying_isin` | TEXT | ISIN of underlying asset for structured/derivative bonds | `IE00B0M63284` | Only populated for structured products, credit-linked notes, etc. Empty for plain bonds |
| `commodity_derivative` | TEXT | Indicates if commodity-linked derivative | `Y` (yes), `N` (no), or empty | Rare; most bonds will be empty or 'N' |

---

### Dates (ISO 8601 Format: YYYY-MM-DD)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `valid_from_date` | TEXT | Date this record version became valid (publication date) | `2026-03-07` |
| `admission_approval_date` | TEXT | Date issuer approved/admitted the bond to trading | `2025-01-15` |
| `request_for_admission_date` | TEXT | Date admission was requested | `2024-12-20` |
| `first_trade_date` | TEXT | Date of first trade (from canonical record) | `2025-02-01` |
| `maturity_date` | TEXT | Bond maturity/redemption date | `2027-01-15` |
| `termination_date` | TEXT | Trading termination/delisting date (if applicable) | Empty for active bonds |

---

### Issuer Information

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `issuer_lei` | TEXT | Legal Entity Identifier of bond issuer (ISO 17442) — 20-char alphanumeric | `5493001KJTIIGC8Y1R12` |
| `issuer_request` | TEXT | Was the issuer the one requesting admission? | `Y`, `N`, or empty |

---

### Regulatory & Administrative

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `relevant_competent_authority` | TEXT | ISO 3166-1 alpha-2 country code or authority name (responsible regulator) | `DE`, `IE`, `LU`, `ESMA`, `BaFin`, `CBI`, `AMF` |
| `source_file` | TEXT | Source FULINS_D XML filename (indicates data release date) | `FULINS_D_20260307_01of04` |

