import json
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/reports/EFERT_Annual_Report_2025.pdf"
OUTPUT = ROOT / "data/processed/EFERT_2025_statements.json"

records = []

with pdfplumber.open(SOURCE) as pdf:
    for page_number in (160, 161, 162):
        page = pdf.pages[page_number - 1]
        midpoint = page.width / 2

        halves = {
            "left": (0, 0, midpoint, page.height),
            "right": (midpoint, 0, page.width, page.height),
        }

        for side, bounds in halves.items():
            text = page.crop(bounds).extract_text() or ""

            if not text.strip():
                raise ValueError(
                    f"No text extracted: page {page_number}, {side}"
                )

            records.append({
                "report": SOURCE.name,
                "scope": "consolidated",
                "page": page_number,
                "side": side,
                "text": text,
            })

            print(f"\n=== PDF page {page_number} | {side} ===")
            print("\n".join(text.splitlines()[:5]))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(
    json.dumps(records, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(f"\nSaved {len(records)} sections to: {OUTPUT}")