from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
URL = "https://dps.psx.com.pk/eligible-scrips"


def main():
    try:
        response = requests.get(URL, timeout=(10, 60))
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Download failed: {exc}")
        print("Database unchanged.")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    matching_tables = []

    for table in soup.find_all("table"):
        headers = [
            cell.get_text(" ", strip=True).lower()
            for cell in table.find_all("th")
        ]

        if "symbol" in headers and "name" in headers:
            matching_tables.append(table)

    if not matching_tables:
        print("No Symbol/Name tables found.")
        print("The page may require JavaScript or have changed.")
        print("Database unchanged.")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    folder = ROOT / "data" / "raw" / "psx"
    folder.mkdir(parents=True, exist_ok=True)

    output = folder / f"eligible_scrips_{timestamp}.html"
    output.write_bytes(response.content)

    print(f"Saved source snapshot: {output}")
    print(f"Matching tables: {len(matching_tables)}")

    for index, table in enumerate(matching_tables, 1):
        rows = [
            [cell.get_text(" ", strip=True)
             for cell in row.find_all("td")]
            for row in table.find_all("tr")
        ]
        rows = [row for row in rows if row]

        print(f"\nTable {index}: {len(rows)} data rows")
        for row in rows[:5]:
            print(row)

    print("\nPreview only — database unchanged.")


if __name__ == "__main__":
    main()