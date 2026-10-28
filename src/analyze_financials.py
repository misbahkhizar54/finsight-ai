import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data/processed/EFERT_2025_financials.json"
OUTPUT_PATH = ROOT / "data/processed/EFERT_2025_analysis.csv"


def percent_change(current, previous):
    if previous == 0:
        raise ValueError("Cannot calculate growth from a zero base.")
    return (current / previous - 1) * 100


def main():
    report = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    if report["scope"] != "consolidated":
        raise ValueError("This analysis expects consolidated figures.")

    if report["default_unit"] != "PKR thousands":
        raise ValueError("Expected financial amounts in PKR thousands.")

    if report["unit_overrides"]["eps"] != "PKR per share":
        raise ValueError("Expected EPS in PKR per share.")

    previous = report["figures"]["2024"]
    current = report["figures"]["2025"]
    pages = report["pdf_pages"]

    metrics = [
        (
            "Revenue growth",
            percent_change(current["sales"], previous["sales"]),
            "%",
            pages["sales"],
        ),
        (
            "Profit growth",
            percent_change(current["profit"], previous["profit"]),
            "%",
            pages["profit"],
        ),
        (
            "EPS growth",
            percent_change(current["eps"], previous["eps"]),
            "%",
            pages["eps"],
        ),
    ]

    for year, figures in (("2025", current), ("2024", previous)):
        if figures["sales"] == 0 or figures["liabilities"] == 0:
            raise ValueError(f"Zero denominator in {year} figures.")

        metrics.extend([
            (
                f"Gross margin {year}",
                figures["gross"] / figures["sales"] * 100,
                "%",
                pages["gross"],
            ),
            (
                f"Net margin {year}",
                figures["profit"] / figures["sales"] * 100,
                "%",
                pages["profit"],
            ),
            (
                f"Current ratio {year}",
                figures["assets"] / figures["liabilities"],
                "x",
                pages["assets"],
            ),
            (
                f"Operating cash flow {year}",
                figures["cash"] / 1_000_000,
                "PKR billion",
                pages["cash"],
            ),
        ])

    print(f"{report['symbol']} consolidated financial analysis")
    print(f"Source: {report['source']}")
    print(f"Input: {INPUT_PATH}\n")

    for name, value, unit, page in metrics:
        print(f"{name}: {value:,.2f} {unit} | PDF page {page}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Metric", "Value", "Unit", "Source", "Scope", "PDF page"
        ])

        for name, value, unit, page in metrics:
            writer.writerow([
                name,
                round(value, 4),
                unit,
                report["source"],
                report["scope"],
                page,
            ])

    print(f"\nSaved analysis to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()