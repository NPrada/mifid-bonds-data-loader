#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "rich",
# ]
# ///

"""
FIRDS Bonds Data Downloader
Downloads the latest weekly FULINS_D (debt/bonds) full reference data files
from the ESMA FIRDS system and extracts them to ./data/

Run with: uv run download_full_reference.py
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import (
    Progress,
    BarColumn,
    DownloadColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

SOLR_URL = "https://registers.esma.europa.eu/solr/esma_registers_firds_files/select"
DATA_DIR = Path("data")
# CFI code first letter 'D' = Debt instruments (bonds, notes, debentures)
BONDS_CFI_PREFIX = "D"

console = Console()


def get_last_saturday(from_date: date | None = None) -> date:
    """Return the most recent Saturday on or before from_date."""
    if from_date is None:
        from_date = date.today()
    # weekday(): Mon=0 ... Sat=5, Sun=6  ->  days_back = (weekday - 5) % 7
    days_back = (from_date.weekday() - 5) % 7
    return from_date - timedelta(days=days_back)


def parse_solr_doc(doc_el: ET.Element) -> dict:
    """Parse a Solr <doc> element into a plain dict."""
    result = {}
    for child in doc_el:
        name = child.get("name")
        if child.tag == "str":
            result[name] = child.text
        elif child.tag in ("int", "long"):
            result[name] = int(child.text or 0)
        elif child.tag == "date":
            result[name] = child.text
        elif child.tag == "arr":
            result[name] = [el.text for el in child]
    return result


def query_solr(pub_date: date, start: int = 0, rows: int = 100) -> tuple[list[dict], int]:
    """Query the ESMA SOLR endpoint for files published on pub_date."""
    date_str = pub_date.strftime("%Y-%m-%d")
    params = {
        "q": "*",
        "fq": f"publication_date:[{date_str}T00:00:00Z TO {date_str}T23:59:59Z]",
        "wt": "xml",
        "indent": "true",
        "start": str(start),
        "rows": str(rows),
    }
    response = httpx.get(SOLR_URL, params=params, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    result_el = root.find("result")
    if result_el is None:
        return [], 0

    num_found = int(result_el.get("numFound", 0))
    docs = [parse_solr_doc(doc) for doc in result_el.findall("doc")]
    return docs, num_found


def get_all_files_for_date(pub_date: date) -> list[dict]:
    """Fetch all file records for a given publication date (handles pagination)."""
    all_docs: list[dict] = []
    start = 0
    rows = 100
    while True:
        docs, num_found = query_solr(pub_date, start=start, rows=rows)
        all_docs.extend(docs)
        start += rows
        if start >= num_found:
            break
    return all_docs


def find_latest_bonds_files(max_weeks_back: int = 8) -> tuple[date, list[dict]]:
    """
    Walk backwards from the most recent Sunday until FULINS_D files are found.
    Returns (publication_date, list_of_file_records).
    """
    candidate = get_last_saturday()
    for _ in range(max_weeks_back):
        console.print(f"  Checking {candidate}...", end="")
        try:
            all_files = get_all_files_for_date(candidate)
        except httpx.HTTPError as exc:
            console.print(f" [yellow]HTTP error: {exc}[/yellow]")
            candidate -= timedelta(weeks=1)
            continue

        bond_files = [
            f for f in all_files
            if (f.get("file_name") or "").startswith(f"FULINS_{BONDS_CFI_PREFIX}_")
        ]
        if bond_files:
            console.print(f" [green]found {len(bond_files)} file(s)[/green]")
            return candidate, bond_files

        console.print(" none found")
        candidate -= timedelta(weeks=1)

    raise RuntimeError(
        f"No FULINS_{BONDS_CFI_PREFIX} files found in the last {max_weeks_back} weeks."
    )


def download_file(url: str, dest: Path) -> None:
    """Stream-download a file with a rich progress bar."""
    with httpx.stream("GET", url, timeout=600, follow_redirects=True) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0)) or None

        with Progress(
            TextColumn("[bold blue]{task.fields[filename]}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("dl", filename=dest.name, total=total)
            with dest.open("wb") as fh:
                for chunk in response.iter_bytes(chunk_size=65536):
                    fh.write(chunk)
                    progress.advance(task, len(chunk))


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract a ZIP archive to extract_to directory."""
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)


def main() -> None:
    console.rule("[bold]FIRDS Bonds Data Downloader[/bold]")
    console.print(f"Output directory : [cyan]{DATA_DIR.resolve()}[/cyan]")
    console.print(f"CFI prefix       : [cyan]FULINS_{BONDS_CFI_PREFIX}[/cyan] (debt instruments)\n")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # --- Discover latest available full-file date ---
    console.print("[bold]Searching for the latest FULINS_D publication...[/bold]")
    try:
        pub_date, bond_files = find_latest_bonds_files()
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(1)

    # --- Print summary table ---
    table = Table(title=f"Files to download  (published {pub_date})", show_lines=True)
    table.add_column("File name", style="cyan")
    table.add_column("Download URL", style="dim", no_wrap=False)
    for f in bond_files:
        table.add_row(f.get("file_name", "?"), f.get("download_link", "?"))
    console.print(table)

    # --- Download and extract ---
    for file_info in bond_files:
        file_name: str = file_info.get("file_name") or file_info.get("id") or "unknown.zip"
        download_url: str | None = file_info.get("download_link")

        if not download_url:
            console.print(f"[yellow]Skipping {file_name}: no download_link in metadata[/yellow]")
            continue

        zip_path = DATA_DIR / file_name
        extract_dir = DATA_DIR / zip_path.stem  # e.g. data/FULINS_D_20250101_01of02/

        # Download
        if zip_path.exists():
            console.print(f"[green]Already downloaded:[/green] {file_name}")
        else:
            console.print(f"\nDownloading [bold]{file_name}[/bold]...")
            try:
                download_file(download_url, zip_path)
                console.print(f"  [green]Saved:[/green] {zip_path}")
            except httpx.HTTPError as exc:
                console.print(f"  [red]Download failed: {exc}[/red]")
                continue

        # Extract
        if extract_dir.exists() and any(extract_dir.iterdir()):
            console.print(f"[green]Already extracted:[/green] {extract_dir.name}/")
        else:
            console.print(f"  Extracting to [cyan]{extract_dir.name}/[/cyan]...")
            extract_zip(zip_path, extract_dir)
            extracted = list(extract_dir.iterdir())
            console.print(f"  [green]Extracted {len(extracted)} file(s)[/green]")

    console.rule("[bold green]Done[/bold green]")
    console.print(f"All data is in [cyan]{DATA_DIR.resolve()}[/cyan]")


if __name__ == "__main__":
    main()
