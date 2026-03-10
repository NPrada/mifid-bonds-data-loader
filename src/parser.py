#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "rich",
# ]
# ///

"""
FIRDS Bonds CSV Parser
Parses all FULINS_D XML files from ./data/ into a single CSV: ./data/bonds.csv

Run with: uv run parser.py
"""

import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from rich.console import Console
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
)

DATA_DIR = Path("data")
OUTPUT_CSV = DATA_DIR / "bonds.csv"

# Namespace for the auth.017.001.02 payload
NS = "urn:iso:std:iso:20022:tech:xsd:auth.017.001.02"

console = Console()

# ---------------------------------------------------------------------------
# CFI code lookup tables (ISO 10962:2019)
# ---------------------------------------------------------------------------

CFI_DEBT_TYPE = {
    "A": "Bonds",
    "B": "Convertible bonds",
    "C": "Bonds with warrants",
    "D": "Medium-term notes (MTN)",
    "E": "Others",
    "F": "Mortgage-backed securities",
    "G": "Asset-backed securities",
    "H": "Municipal bonds",
    "I": "Covered bonds",
    "J": "Depositary receipts on debt",
}

CFI_INTEREST_TYPE = {
    "F": "Fixed rate",
    "V": "Variable/floating rate",
    "Z": "Zero coupon",
    "A": "Adjustable/other rate",
    "N": "Not applicable",
}

CFI_GUARANTEE = {
    "G": "Government guaranteed",
    "J": "Joint guaranteed",
    "Y": "Third-party guaranteed",
    "N": "Not guaranteed",
}

CFI_REDEMPTION = {
    "A": "At maturity (bullet)",
    "B": "Callable",
    "C": "Puttable",
    "D": "Extendible",
    "F": "Fixed periodic redemption",
    "G": "Other",
    "R": "Redeemable at choice",
}

CFI_FORM = {
    "B": "Bearer",
    "R": "Registered",
    "S": "Bearer and Registered",
    "N": "Nominee/other",
}

DEBT_SENIORITY = {
    "SNDB": "Senior debt",
    "SBOD": "Subordinated debt",
    "JUND": "Junior debt",
}

CSV_COLUMNS = [
    "id",
    "isin",
    "trading_venue_mic",
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


def p(*tags: str) -> str:
    """Build a namespace-qualified ElementTree path."""
    return "/".join(f"{{{NS}}}{t}" for t in tags)


def txt(elem: ET.Element, *tags: str) -> str:
    """Return text of a nested element, or empty string if absent."""
    found = elem.find(p(*tags))
    return (found.text or "").strip() if found is not None else ""


def attr(elem: ET.Element, path_tags: tuple, attribute: str) -> str:
    """Return an attribute of a nested element, or empty string."""
    found = elem.find(p(*path_tags))
    return (found.get(attribute) or "").strip() if found is not None else ""


def decode_cfi(cfi: str) -> dict:
    """Expand a 6-char CFI code into human-readable column values."""
    if len(cfi) != 6:
        return {
            "cfi_debt_type": "",
            "cfi_interest_type": "",
            "cfi_guarantee": "",
            "cfi_redemption": "",
            "cfi_form": "",
        }
    return {
        "cfi_debt_type":     CFI_DEBT_TYPE.get(cfi[1], cfi[1]),
        "cfi_interest_type": CFI_INTEREST_TYPE.get(cfi[2], cfi[2]),
        "cfi_guarantee":     CFI_GUARANTEE.get(cfi[3], cfi[3]),
        "cfi_redemption":    CFI_REDEMPTION.get(cfi[4], cfi[4]),
        "cfi_form":          CFI_FORM.get(cfi[5], cfi[5]),
    }


def parse_record(elem: ET.Element, source_file: str) -> dict:
    """Extract all fields from a single <RefData> element into a flat dict."""
    # --- General attributes ---
    isin     = txt(elem, "FinInstrmGnlAttrbts", "Id")
    full_nm  = txt(elem, "FinInstrmGnlAttrbts", "FullNm")
    shrt_nm  = txt(elem, "FinInstrmGnlAttrbts", "ShrtNm")
    cfi      = txt(elem, "FinInstrmGnlAttrbts", "ClssfctnTp")
    ntnl_ccy = txt(elem, "FinInstrmGnlAttrbts", "NtnlCcy")
    cmmdty   = txt(elem, "FinInstrmGnlAttrbts", "CmmdtyDerivInd")

    # --- Issuer ---
    issr_lei = txt(elem, "Issr")

    # --- Trading venue ---
    tv_mic      = txt(elem, "TradgVnRltdAttrbts", "Id")
    issr_req    = txt(elem, "TradgVnRltdAttrbts", "IssrReq")
    admsn_dt    = txt(elem, "TradgVnRltdAttrbts", "AdmssnApprvlDtByIssr")
    req_admsn   = txt(elem, "TradgVnRltdAttrbts", "ReqForAdmssnDt")
    frst_trd    = txt(elem, "TradgVnRltdAttrbts", "FrstTradDt")
    termntn     = txt(elem, "TradgVnRltdAttrbts", "TermntnDt")

    # --- Debt attributes ---
    ttl_nmnl      = txt(elem, "DebtInstrmAttrbts", "TtlIssdNmnlAmt")
    ttl_nmnl_ccy  = attr(elem, ("DebtInstrmAttrbts", "TtlIssdNmnlAmt"), "Ccy")
    mtrty         = txt(elem, "DebtInstrmAttrbts", "MtrtyDt")
    nmnl_unit     = txt(elem, "DebtInstrmAttrbts", "NmnlValPerUnit")
    nmnl_unit_ccy = attr(elem, ("DebtInstrmAttrbts", "NmnlValPerUnit"), "Ccy")
    debt_snrty    = txt(elem, "DebtInstrmAttrbts", "DebtSnrty")

    # --- Interest rate ---
    fxd_el  = elem.find(p("DebtInstrmAttrbts", "IntrstRate", "Fxd"))
    fltg_el = elem.find(p("DebtInstrmAttrbts", "IntrstRate", "Fltg"))

    if fxd_el is not None:
        rate_type        = "fixed"
        fixed_rate       = (fxd_el.text or "").strip()
        fltg_ref_isin    = ""
        fltg_term_val    = ""
        fltg_term_unit   = ""
        fltg_spread      = ""
    elif fltg_el is not None:
        rate_type        = "floating"
        fixed_rate       = ""
        fltg_ref_isin    = txt(fltg_el, "RefRate", "ISIN")
        fltg_term_val    = txt(fltg_el, "Term", "Val")
        fltg_term_unit   = txt(fltg_el, "Term", "Unit")
        fltg_spread      = txt(fltg_el, "BsisPtSprd")
    else:
        rate_type = fixed_rate = fltg_ref_isin = fltg_term_val = fltg_term_unit = fltg_spread = ""

    # --- Underlying (structured products) ---
    undrlg_bskt = txt(elem, "DerivInstrmAttrbts", "UndrlygInstrm", "Bskt", "ISIN")
    undrlg_sngl = txt(elem, "DerivInstrmAttrbts", "UndrlygInstrm", "Sngl", "ISIN")
    underlying  = undrlg_bskt or undrlg_sngl

    # --- Technical attributes ---
    nca            = txt(elem, "TechAttrbts", "RlvntCmptntAuthrty")
    valid_from     = txt(elem, "TechAttrbts", "PblctnPrd", "FrDt")
    rlvnt_tv       = txt(elem, "TechAttrbts", "RlvntTradgVn")

    cfi_decoded = decode_cfi(cfi)

    return {
        "id":                            f"{isin}-{tv_mic}",
        "isin":                          isin,
        "trading_venue_mic":             tv_mic,
        "full_name":                     full_nm,
        "short_name":                    shrt_nm,
        "cfi_code":                      cfi,
        "cfi_debt_type":                 cfi_decoded["cfi_debt_type"],
        "cfi_interest_type":             cfi_decoded["cfi_interest_type"],
        "cfi_guarantee":                 cfi_decoded["cfi_guarantee"],
        "cfi_redemption":                cfi_decoded["cfi_redemption"],
        "cfi_form":                      cfi_decoded["cfi_form"],
        "notional_currency":             ntnl_ccy,
        "commodity_derivative":          cmmdty,
        "issuer_lei":                    issr_lei,
        "issuer_request":                issr_req,
        "admission_approval_date":       admsn_dt,
        "request_for_admission_date":    req_admsn,
        "first_trade_date":              frst_trd,
        "termination_date":              termntn,
        "total_issued_nominal_amount":   ttl_nmnl,
        "total_issued_nominal_currency": ttl_nmnl_ccy,
        "maturity_date":                 mtrty,
        "nominal_value_per_unit":        nmnl_unit,
        "nominal_value_currency":        nmnl_unit_ccy,
        "interest_rate_type":            rate_type,
        "fixed_rate":                    fixed_rate,
        "floating_ref_rate_isin":        fltg_ref_isin,
        "floating_ref_rate_term_value":  fltg_term_val,
        "floating_ref_rate_term_unit":   fltg_term_unit,
        "floating_spread_bps":           fltg_spread,
        "debt_seniority":                debt_snrty,
        "debt_seniority_label":          DEBT_SENIORITY.get(debt_snrty, debt_snrty),
        "underlying_isin":               underlying,
        "relevant_competent_authority":  nca,
        "valid_from_date":               valid_from,
        "relevant_trading_venue":        rlvnt_tv,
        "source_file":                   source_file,
    }


def parse_xml(xml_path: Path, writer: csv.DictWriter, progress, task) -> int:
    """Stream-parse a single XML file and write rows to the CSV writer."""
    source_file = xml_path.stem
    ref_tag = f"{{{NS}}}RefData"
    count = 0

    context = ET.iterparse(xml_path, events=("start", "end"))
    _, root = next(context)  # grab root element so we can clear it

    for event, elem in context:
        if event == "end" and elem.tag == ref_tag:
            row = parse_record(elem, source_file)
            writer.writerow(row)
            count += 1
            root.clear()  # free memory — discard processed children
            if count % 10_000 == 0:
                progress.advance(task, 10_000)

    # advance remaining
    remainder = count % 10_000
    if remainder:
        progress.advance(task, remainder)

    return count


def sort_csv_by_id() -> None:
    """Read the CSV, sort by id column, and write back."""
    console.print("\n[bold blue]Sorting CSV by id...[/bold blue]")

    # Read all rows
    with OUTPUT_CSV.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    # Sort by id
    rows.sort(key=lambda row: row["id"])

    # Write back
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    console.print("[green]✓ CSV sorted by id[/green]")


def main() -> None:
    xml_files = sorted(DATA_DIR.glob("*/*.xml"))
    if not xml_files:
        console.print(f"[red]No XML files found under {DATA_DIR}/[/red]")
        sys.exit(1)

    console.rule("[bold]FIRDS Bonds CSV Parser[/bold]")
    console.print(f"Found [bold]{len(xml_files)}[/bold] XML file(s) to parse")
    console.print(f"Output : [cyan]{OUTPUT_CSV}[/cyan]\n")

    total_rows = 0

    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()

        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            for xml_path in xml_files:
                size_mb = xml_path.stat().st_size / 1_048_576
                task = progress.add_task(
                    f"{xml_path.parent.name}",
                    total=None,  # unknown until parsed
                )
                console.print(f"  Parsing [cyan]{xml_path.name}[/cyan] ({size_mb:.0f} MB)...")
                n = parse_xml(xml_path, writer, progress, task)
                progress.update(task, total=n, completed=n)
                console.print(f"  [green]{n:,} records[/green]")
                total_rows += n

    # Sort the CSV by id
    sort_csv_by_id()

    output_mb = OUTPUT_CSV.stat().st_size / 1_048_576
    console.rule("[bold green]Done[/bold green]")
    console.print(f"Total records : [bold]{total_rows:,}[/bold]")
    console.print(f"Output file   : [cyan]{OUTPUT_CSV}[/cyan] ({output_mb:.1f} MB)")


if __name__ == "__main__":
    main()
