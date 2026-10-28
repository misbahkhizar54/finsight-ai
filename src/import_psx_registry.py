import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/finsight.db"
RAW_FOLDER = ROOT / "data/raw/psx"
SOURCE_URL = "https://dps.psx.com.pk/eligible-scrips"


def main():
    snapshots = sorted(RAW_FOLDER.glob("eligible_scrips_*.html"))

    if not snapshots:
        raise FileNotFoundError("Run fetch_psx_registry.py first.")

    if not DB_PATH.exists():
        raise FileNotFoundError("Run init_db.py first.")

    snapshot = snapshots[-1]
    soup = BeautifulSoup(snapshot.read_bytes(), "html.parser")
    entries = {}
    table_number = 0
    total_rows = 0

    for table in soup.find_all("table"):
        headers = [
            cell.get_text(" ", strip=True).lower()
            for cell in table.find_all("th")
        ]

        if "symbol" not in headers or "name" not in headers:
            continue

        table_number += 1
        symbol_index = headers.index("symbol")
        name_index = headers.index("name")

        for row in table.find_all("tr"):
            cells = [
                cell.get_text(" ", strip=True)
                for cell in row.find_all("td")
            ]

            if len(cells) <= max(symbol_index, name_index):
                continue

            symbol = cells[symbol_index].strip()
            name = cells[name_index].strip()

            if not symbol or not name:
                continue

            total_rows += 1

            # Keep different names for the same symbol as separate candidates.
            key = (symbol, name)
            entries.setdefault(key, set()).add(table_number)

    if not entries:
        raise ValueError("No usable entries found. Database unchanged.")

    imported_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS registry_candidates (
                id INTEGER PRIMARY KEY,
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                security_name TEXT NOT NULL,
                source_tables TEXT NOT NULL,
                source_url TEXT NOT NULL,
                snapshot_path TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'pending',
                UNIQUE(exchange, symbol, security_name, snapshot_path)
            )
        """)

        connection.executemany("""
            INSERT INTO registry_candidates (
                exchange, symbol, security_name, source_tables,
                source_url, snapshot_path, imported_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(
                exchange, symbol, security_name, snapshot_path
            ) DO NOTHING
        """, [
            (
                "PSX",
                symbol,
                name,
                json.dumps(sorted(table_numbers)),
                SOURCE_URL,
                snapshot.relative_to(ROOT).as_posix(),
                imported_at,
            )
            for (symbol, name), table_numbers in sorted(entries.items())
        ])

    symbol_names = {}
    for symbol, name in entries:
        symbol_names.setdefault(symbol, set()).add(name)

    conflicts = {
        symbol: names
        for symbol, names in symbol_names.items()
        if len(names) > 1
    }

    print(f"Source: {snapshot.name}")
    print(f"Total source rows: {total_rows}")
    print(f"Distinct symbol/name candidates: {len(entries)}")
    print(f"Repeated rows combined: {total_rows - len(entries)}")
    print(f"Symbols with multiple names: {len(conflicts)}")
    print("Snapshot imported; rerunning it will not duplicate records.")
    print("Verified companies table unchanged.")


if __name__ == "__main__":
    main()