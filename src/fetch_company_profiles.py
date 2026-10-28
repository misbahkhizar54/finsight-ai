import argparse
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/finsight.db"
RAW_FOLDER = ROOT / "data/raw/psx/profiles"


def parse_profile(html, expected_symbol):
    soup = BeautifulSoup(html, "html.parser")

    symbol_node = soup.select_one(".pageHeader__title")
    name_node = soup.select_one(".quote__name")

    if symbol_node is None or name_node is None:
        raise ValueError("Company identity fields not found.")

    actual_symbol = symbol_node.get_text(" ", strip=True)
    if actual_symbol.upper() != expected_symbol:
        raise ValueError(
            f"Symbol mismatch: expected {expected_symbol}, "
            f"received {actual_symbol}"
        )

    name = name_node.get_text(" ", strip=True)
    if not name:
        raise ValueError("Company name is empty.")

    website = None

    for heading in soup.select(".profile__item .item__head"):
        if heading.get_text(" ", strip=True).upper() != "WEBSITE":
            continue

        paragraph = heading.find_next_sibling("p")
        link = paragraph.find("a", href=True) if paragraph else None

        if link:
            candidate = link["href"].strip()
            parsed = urlparse(candidate)

            if parsed.scheme in {"http", "https"} and parsed.hostname:
                website = candidate

        break

    return name, website


def parse_officers(html):
    """Read only table rows inside PSX's KEY PEOPLE profile item.

    This is a source observation, not a complete board or an appointment record.
    """
    soup = BeautifulSoup(html, "html.parser")
    officers = []
    seen = set()
    found = False
    invalid = False
    for heading in soup.select(".profile__item .item__head"):
        if heading.get_text(" ", strip=True).upper() != "KEY PEOPLE":
            continue
        found = True
        item = heading.find_parent(class_="profile__item")
        for row in item.select("table tr"):
            cells = row.find_all("td", recursive=False)
            if not cells:
                continue
            if len(cells) != 2:
                invalid = True
                continue
            name, role = [" ".join(c.get_text(" ", strip=True).split()) for c in cells]
            if not name or not role or name.lower() in {"-", "n/a", "not available"}:
                invalid = True
                continue
            key = (name.casefold(), role.casefold())
            if key not in seen:
                seen.add(key)
                officers.append((name, role))
    status = "parsed" if officers and not invalid else "needs_review" if found else "not_found"
    return officers, status


def init_officer_tables(connection):
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS company_officer_snapshots (
            id INTEGER PRIMARY KEY,
            company_id INTEGER NOT NULL REFERENCES companies(id),
            source_url TEXT NOT NULL,
            raw_path TEXT NOT NULL UNIQUE,
            fetched_at TEXT NOT NULL,
            source_as_of TEXT,
            parse_status TEXT NOT NULL
                CHECK(parse_status IN ('parsed', 'needs_review', 'not_found'))
        );
        CREATE TABLE IF NOT EXISTS company_officers (
            snapshot_id INTEGER NOT NULL REFERENCES company_officer_snapshots(id),
            person_name TEXT NOT NULL,
            designation TEXT NOT NULL,
            PRIMARY KEY(snapshot_id, person_name, designation)
        );
    """)


def save_officers(connection, company_id, url, raw_path, fetched_at, officers, status):
    """Append evidence; never infer resignations or delete earlier observations."""
    connection.execute("""
        INSERT INTO company_officer_snapshots
            (company_id, source_url, raw_path, fetched_at, parse_status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(raw_path) DO NOTHING
    """, (company_id, url, raw_path, fetched_at, status))
    snapshot_id = connection.execute(
        "SELECT id FROM company_officer_snapshots WHERE raw_path = ?", (raw_path,)
    ).fetchone()[0]
    connection.executemany("""
        INSERT INTO company_officers(snapshot_id, person_name, designation)
        VALUES (?, ?, ?) ON CONFLICT DO NOTHING
    """, [(snapshot_id, name, role) for name, role in officers])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="+")
    args = parser.parse_args()

    symbols = list(dict.fromkeys(s.upper() for s in args.symbols))

    if any(not re.fullmatch(r"[A-Z0-9]+", s) for s in symbols):
        raise ValueError("Use plain symbols, such as EFERT ABL SYS.")

    if not DB_PATH.exists():
        raise FileNotFoundError("Run init_db.py first.")

    RAW_FOLDER.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        init_officer_tables(connection)

        latest = connection.execute("""
            SELECT MAX(snapshot_path)
            FROM market_snapshots
            WHERE exchange = 'PSX' AND market_code = 'REG'
        """).fetchone()[0]

        regular_symbols = {
            row[0]
            for row in connection.execute("""
                SELECT symbol
                FROM security_market_memberships
                WHERE snapshot_path = ?
                  AND exchange = 'PSX'
                  AND market_code = 'REG'
            """, (latest,))
        }

        with requests.Session() as session:
            for index, symbol in enumerate(symbols):
                if symbol not in regular_symbols:
                    print(f"{symbol}: skipped — absent from latest REG snapshot.")
                    continue

                if index:
                    time.sleep(2)

                url = f"https://dps.psx.com.pk/company/{symbol}"

                try:
                    response = session.get(url, timeout=(10, 60))

                    if response.status_code in {403, 429}:
                        print(
                            f"{symbol}: HTTP {response.status_code}. "
                            "Stopping this batch."
                        )
                        break

                    response.raise_for_status()

                    if urlparse(response.url).hostname != "dps.psx.com.pk":
                        raise ValueError("Unexpected redirect destination.")

                    name, website = parse_profile(response.content, symbol)
                    officers, officer_status = parse_officers(response.content)

                except (requests.RequestException, ValueError) as exc:
                    print(f"{symbol}: failed — {exc}")
                    continue

                now = datetime.now(timezone.utc)
                stamp = now.strftime("%Y%m%dT%H%M%S%fZ")
                raw_path = RAW_FOLDER / f"{symbol}_{stamp}.html"
                raw_path.write_bytes(response.content)

                # Preserve an existing website if this fetch found none.
                with connection:
                    connection.execute("""
                        INSERT INTO companies (
                            exchange, symbol, company_name,
                            official_website, registry_source_url,
                            registry_checked_at
                        )
                        VALUES ('PSX', ?, ?, ?, ?, ?)
                        ON CONFLICT(exchange, symbol) DO UPDATE SET
                            company_name = excluded.company_name,
                            official_website = COALESCE(
                                excluded.official_website,
                                companies.official_website
                            ),
                            registry_source_url = excluded.registry_source_url,
                            registry_checked_at = excluded.registry_checked_at
                    """, (symbol, name, website, url, now.isoformat()))

                    company_id = connection.execute("""
                        SELECT id FROM companies
                        WHERE exchange = 'PSX' AND symbol = ?
                    """, (symbol,)).fetchone()[0]

                    connection.execute("""
                        INSERT INTO company_logos (company_id, status)
                        VALUES (?, 'pending')
                        ON CONFLICT(company_id) DO NOTHING
                    """, (company_id,))

                    save_officers(
                        connection, company_id, url,
                        raw_path.relative_to(ROOT).as_posix(), now.isoformat(),
                        officers, officer_status,
                    )

                print(f"{symbol}: {name}")
                print(f"  Website from PSX: {website or 'Not found'}")
                print("  Profile saved; existing logo settings preserved.")
                print(f"  Key People: {len(officers)} rows | {officer_status}")
                for person, role in officers:
                    print(f"    {person} | {role}")
                if officer_status != "parsed":
                    print("  Check saved HTML; previous officer observations are preserved.")
                print("  Fetch time is not an appointment date; full board coverage is not assumed.")


if __name__ == "__main__":
    main()