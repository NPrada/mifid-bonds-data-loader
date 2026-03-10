# CSV Schema — ESMA FIRDS Bonds Reference Data

Source: ISO 20022 `auth.017.001.02` (MiFIR RTS 23 full reference data file, FULINS_D)

Each row represents one **(ISIN, trading venue)** combination. The same ISIN can appear
multiple times if it is admitted to trading on multiple venues.

---

## Primary Key

| Column | Description |
|---|---|
| `id` | Composite key: `{isin}-{trading_venue_mic}` — unique per row |

---

## General Instrument Attributes
Source: `<FinInstrmGnlAttrbts>`

| Column | XML tag | Description |
|---|---|---|
| `isin` | `Id` | ISIN code (12-char alphanumeric, ISO 6166) |
| `full_name` | `FullNm` | Full legal instrument name (up to 350 chars) |
| `short_name` | `ShrtNm` | Short name (up to 35 chars, Bloomberg-style) |
| `cfi_code` | `ClssfctnTp` | Raw 6-character CFI code (ISO 10962) — see CFI columns below |
| `notional_currency` | `NtnlCcy` | Notional/settlement currency (ISO 4217, e.g. `EUR`, `GBP`) |
| `commodity_derivative` | `CmmdtyDerivInd` | `true` if classified as a commodity derivative, else `false` |

---

## CFI Code Breakdown
Source: `<ClssfctnTp>` decoded per ISO 10962:2019

Position 1 is always `D` (Debt) — it is not included as a column since this file only contains debt instruments.

| Column | CFI Position | Description & Values |
|---|---|---|
| `cfi_debt_type` | 2 | Type of debt instrument: `A`=Bonds · `B`=Convertible bonds · `C`=Bonds with warrants · `D`=Medium-term notes (MTN) · `E`=Others · `F`=Mortgage-backed securities · `G`=Asset-backed securities · `H`=Municipal bonds · `I`=Covered bonds · `J`=Depositary receipts on debt |
| `cfi_interest_type` | 3 | Coupon/interest type: `F`=Fixed rate · `V`=Variable/floating rate · `Z`=Zero coupon · `A`=Adjustable/other · `N`=Not applicable |
| `cfi_guarantee` | 4 | Guarantee status: `G`=Government guaranteed · `J`=Joint guaranteed · `Y`=Third-party guaranteed · `N`=Not guaranteed |
| `cfi_redemption` | 5 | Redemption/repayment type: `A`=At maturity (bullet) · `B`=Callable (issuer can redeem early) · `C`=Puttable (holder can redeem early) · `D`=Extendible · `F`=Fixed periodic redemption · `G`=Other · `R`=Redeemable at choice |
| `cfi_form` | 6 | Form of issuance: `B`=Bearer · `R`=Registered · `S`=Bearer and Registered · `N`=Nominee/other |

---

## Issuer

| Column | XML tag | Description |
|---|---|---|
| `issuer_lei` | `Issr` | LEI (Legal Entity Identifier) of the issuer — 20-char alphanumeric (ISO 17442) |

---

## Trading Venue Attributes
Source: `<TradgVnRltdAttrbts>`

| Column | XML tag | Description |
|---|---|---|
| `trading_venue_mic` | `Id` | MIC code of the trading venue (ISO 10383, e.g. `XLON`, `XPAR`) |
| `issuer_request` | `IssrReq` | `true` if the issuer requested admission to trading, `false` if venue-initiated |
| `admission_approval_date` | `AdmssnApprvlDtByIssr` | Date the issuer approved admission (ISO 8601 datetime, optional) |
| `request_for_admission_date` | `ReqForAdmssnDt` | Date the request for admission was submitted (ISO 8601 datetime, optional) |
| `first_trade_date` | `FrstTradDt` | Date and time of the first trade on this venue (ISO 8601 datetime) |
| `termination_date` | `TermntnDt` | Date and time the instrument ceased trading on this venue (ISO 8601 datetime, optional) |

---

## Debt Instrument Attributes
Source: `<DebtInstrmAttrbts>`

| Column | XML tag | Description |
|---|---|---|
| `total_issued_nominal_amount` | `TtlIssdNmnlAmt` | Total face value of all units issued (numeric) |
| `total_issued_nominal_currency` | `TtlIssdNmnlAmt@Ccy` | Currency of the total nominal amount (ISO 4217) |
| `maturity_date` | `MtrtyDt` | Date the bond matures / principal is repaid (YYYY-MM-DD) |
| `nominal_value_per_unit` | `NmnlValPerUnit` | Face value of a single unit/bond (numeric) |
| `nominal_value_currency` | `NmnlValPerUnit@Ccy` | Currency of the nominal value per unit (ISO 4217) |
| `interest_rate_type` | derived | `fixed` or `floating` — derived from presence of `<Fxd>` vs `<Fltg>` |
| `fixed_rate` | `IntrstRate/Fxd` | Fixed annual coupon rate as a percentage (e.g. `5.659` means 5.659%). Only set when `interest_rate_type=fixed` |
| `floating_ref_rate_isin` | `IntrstRate/Fltg/RefRate/ISIN` | ISIN of the reference rate index (e.g. `EU0009652783` = Euribor). Only set when `interest_rate_type=floating` |
| `floating_ref_rate_term_value` | `IntrstRate/Fltg/Term/Val` | Numeric tenor of the reference rate (e.g. `3`). Only set when floating |
| `floating_ref_rate_term_unit` | `IntrstRate/Fltg/Term/Unit` | Unit of the tenor: `MNTH`=months · `DAYS`=days. Only set when floating |
| `floating_spread_bps` | `IntrstRate/Fltg/BsisPtSprd` | Spread added to the reference rate in basis points (e.g. `120` = +1.20%). Only set when floating |
| `debt_seniority` | `DebtSnrty` | Seniority code: `SNDB`=Senior debt · `SBOD`=Subordinated debt · `JUND`=Junior debt |

---

## Derivative / Structured Product Attributes
Source: `<DerivInstrmAttrbts>` — only present on structured debt (e.g. credit-linked notes)

| Column | XML tag | Description |
|---|---|---|
| `underlying_isin` | `UndrlygInstrm/Bskt/ISIN` or `UndrlygInstrm/Sngl/ISIN` | ISIN of the underlying instrument or basket reference. Empty for plain bonds |

---

## Technical / Administrative Attributes
Source: `<TechAttrbts>`

| Column | XML tag | Description |
|---|---|---|
| `relevant_competent_authority` | `RlvntCmptntAuthrty` | ISO 3166-1 alpha-2 country code of the National Competent Authority (NCA) responsible for this instrument (e.g. `DE`=BaFin, `IE`=CBI, `LU`=CSSF) |
| `valid_from_date` | `PblctnPrd/FrDt` | Date from which this version of the record is valid (YYYY-MM-DD). Use as `ValidFromDate` when building a historical database |
| `relevant_trading_venue` | `RlvntTradgVn` | MIC of the primary relevant trading venue (used for regulatory reporting purposes; may differ from `trading_venue_mic`) |

---

## Provenance

| Column | Description |
|---|---|
| `source_file` | Name of the source ZIP/XML file this record was parsed from (e.g. `FULINS_D_20260307_01of04`) |
