
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
import argparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/kse100_website_manual_review.csv"
OUTPUT = ROOT / "data/processed/kse100_psx_website_evidence.csv"
RAW_FOLDER = ROOT / "data/raw/psx/website_evidence"

BASE_URL = "https://dps.psx.com.pk/company/"
DELAY_SECONDS = 2
TIMEOUT = (10, 30)


def parse_profile(html, expected_symbol):
    soup = BeautifulSoup(html, "html.parser")

    symbol_node = soup.select_one(".pageHeader__title")
    name_node = soup.select_one(".quote__name")

    if symbol_node is None or name_node is None:
        raise ValueError("PSX profile identity fields not found")

    actual_symbol = symbol_node.get_text(" ", strip=True).upper()
    if actual_symbol != expected_symbol.upper():
        raise ValueError(
            f"Symbol mismatch: expected {expected_symbol}, got {actual_symbol}"
        )

    company_name = name_node.get_text(" ", strip=True)
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

    return company_name, website


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing input CSV: {SOURCE}")

    RAW_FOLDER.mkdir(parents=True, exist_ok=True)

    review = pd.read_csv(SOURCE)
    all_symbols = (
        review["symbol"].dropna().astype(str).str.strip().str.upper()
        .drop_duplicates().tolist()
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="+")
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()

    symbols = (
        [s.strip().upper() for s in args.symbols]
        if args.symbols
        else all_symbols
    )

    unknown = set(symbols) - set(all_symbols)
    if unknown:
        raise ValueError(f"Symbols not found in review CSV: {sorted(unknown)}")

    output_path = Path(args.output)

    results = []
    session = requests.Session()
    session.headers.update({
        "User-Agent": "FinSightAI-Research/1.0 (PSX company profile verification)"
    })

    for index, symbol in enumerate(symbols, start=1):
        url = BASE_URL + symbol
        checked_at = datetime.now(timezone.utc).isoformat()

        row = {
            "symbol": symbol,
            "psx_profile_url": url,
            "psx_company_name": None,
            "psx_website": None,
            "http_status": None,
            "checked_at_utc": checked_at,
            "result": None,
            "raw_html_path": None,
        }

        try:
            response = session.get(url, timeout=TIMEOUT)
            row["http_status"] = response.status_code

            if response.status_code in {403, 429}:
                row["result"] = f"PSX BLOCKED - HTTP {response.status_code}"
                results.append(row)
                print(f"{index}/{len(symbols)} {symbol}: {row['result']}")
                print("Stopping to avoid repeated requests to a blocked source.")
                break

            response.raise_for_status()

            if urlparse(response.url).hostname != "dps.psx.com.pk":
                raise ValueError("Unexpected redirect destination")

            name, website = parse_profile(response.content, symbol)
            row["psx_company_name"] = name
            row["psx_website"] = website
            row["result"] = (
                "PROFILE PARSED - WEBSITE FOUND"
                if website else "PROFILE PARSED - NO WEBSITE LISTED"
            )

            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            raw_path = RAW_FOLDER / f"{symbol}_{stamp}.html"
            raw_path.write_bytes(response.content)
            row["raw_html_path"] = raw_path.relative_to(ROOT).as_posix()

        except (requests.RequestException, ValueError) as exc:
            row["result"] = f"ERROR: {type(exc).__name__}: {exc}"

        results.append(row)
        print(f"{index}/{len(symbols)} {symbol}: {row['result']}")

        if index < len(symbols):
            time.sleep(DELAY_SECONDS)

    pd.DataFrame(results).to_csv(output_path, index=False, encoding="utf-8-sig")
    print("\nEvidence report saved:", output_path)
    print("Profiles recorded:", len(results))
    print("Database was not opened or modified.")


if __name__ == "__main__":
    main()
