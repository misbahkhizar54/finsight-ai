import sqlite3
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/finsight.db"
RAW_FOLDER = ROOT / "data/raw/psx"


def parse_snapshot(path):
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    markets = {}
    memberships = {}

    for panel in soup.select(".tabs__panel[data-name]"):
        code = panel["data-name"]
        heading = panel.find("h2")
        table = panel.find("table")

        if heading is None or table is None:
            continue

        headers = [
            cell.get_text(" ", strip=True).lower()
            for cell in table.find_all("th")
        ]

        if "symbol" not in headers or "name" not in headers:
            continue

        if code in markets:
            raise ValueError(f"Duplicate market panel: {code}")

        markets[code] = heading.get_text(" ", strip=True)
        symbol_index = headers.index("symbol")
        name_index = headers.index("name")

        for row in table.find_all("tr"):
            cells = [
                cell.get_text(" ", strip=True)
                for cell in row.find_all("td")
            ]
            if not cells:
                continue

            if len(cells) <= max(symbol_index, name_index):
                raise ValueError(f"Malformed row in market {code}")

            symbol = cells[symbol_index]
            name = cells[name_index]

            if not symbol or not name:
                raise ValueError(f"Empty symbol/name in market {code}")

            key = (code, symbol)
            if key in memberships and memberships[key] != name:
                raise ValueError(f"Conflicting names for {code}/{symbol}")

            memberships[key] = name

    if "REG" not in markets or not memberships:
        raise ValueError("Expected market structure not found.")

    return markets, memberships


def main():
    snapshots = sorted(RAW_FOLDER.glob("eligible_scrips_*.html"))
    if not snapshots:
        raise FileNotFoundError("Run fetch_psx_registry.py first.")
    if not DB_PATH.exists():
        raise FileNotFoundError("Run init_db.py first.")

    snapshot = snapshots[-1]
    markets, memberships = parse_snapshot(snapshot)
    snapshot_key = snapshot.relative_to(ROOT).as_posix()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executescript("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                snapshot_path TEXT NOT NULL,
                exchange TEXT NOT NULL,
                market_code TEXT NOT NULL,
                market_name TEXT NOT NULL,
                PRIMARY KEY(snapshot_path, exchange, market_code)
            );

            CREATE TABLE IF NOT EXISTS security_market_memberships (
                snapshot_path TEXT NOT NULL,
                exchange TEXT NOT NULL,
                market_code TEXT NOT NULL,
                symbol TEXT NOT NULL,
                security_name TEXT NOT NULL,
                PRIMARY KEY(
                    snapshot_path, exchange, market_code, symbol
                ),
                FOREIGN KEY(snapshot_path, exchange, market_code)
                    REFERENCES market_snapshots(
                        snapshot_path, exchange, market_code
                    )
            );
        """)

        connection.executemany("""
            INSERT INTO market_snapshots
                (snapshot_path, exchange, market_code, market_name)
            VALUES (?, 'PSX', ?, ?)
            ON CONFLICT DO NOTHING
        """, [
            (snapshot_key, code, name)
            for code, name in markets.items()
        ])

        connection.executemany("""
            INSERT INTO security_market_memberships
                (snapshot_path, exchange, market_code,
                 symbol, security_name)
            VALUES (?, 'PSX', ?, ?, ?)
            ON CONFLICT DO NOTHING
        """, [
            (snapshot_key, code, symbol, name)
            for (code, symbol), name in memberships.items()
        ])

    print(f"Snapshot: {snapshot.name}")

    for code, name in markets.items():
        count = sum(
            market_code == code
            for market_code, symbol in memberships
        )
        print(f"{code}: {count} | {name}")

    print(f"\nSaved market memberships: {len(memberships)}")
    print("Existing company records and logos unchanged.")


if __name__ == "__main__":
    main()