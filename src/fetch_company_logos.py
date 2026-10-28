import argparse
import hashlib
import io
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/finsight.db"
LOGO_FOLDER = ROOT / "data/logos"
MAX_BYTES = 5 * 1024 * 1024


def download(session, url):
    """Download with a size limit; preserve TLS verification."""
    with session.get(url, timeout=(10, 30), stream=True) as response:
        response.raise_for_status()
        chunks = []
        size = 0

        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("Download exceeds 5 MB.")
            chunks.append(chunk)

        return b"".join(chunks), response.url


def find_candidates(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    candidates = {}

    for image in soup.find_all("img"):
        description = " ".join([
            image.get("alt", ""),
            image.get("id", ""),
            " ".join(image.get("class", [])),
            image.get("src", ""),
            image.get("data-src", ""),
        ]).lower()

        if "logo" not in description:
            continue
        if any(word in description for word in (
            "forbes", "award", "badge", "partner",
            "certification", "client"
        )):
            continue

        score = 10
        if image.find_parent(["header", "nav"]):
            score += 10

        for attribute in ("data-src", "src"):
            source = image.get(attribute)
            if not source:
                continue

            url = urljoin(base_url, source)
            if urlparse(url).scheme not in {"http", "https"}:
                continue

            candidates[url] = max(candidates.get(url, 0), score)

    return sorted(candidates, key=candidates.get, reverse=True)


def save_image(content, company_id):
    """Save simple SVG logos or convert raster images to PNG."""
    digest = hashlib.sha256(content).hexdigest()[:12]

    # Attempt XML parsing to identify SVG content.
    root = None
    if content.lstrip().startswith(b"<"):
        if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
            raise ValueError("SVG with document/entity declarations skipped.")

        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            pass

    if root is not None:
        if root.tag.split("}")[-1] != "svg":
            raise ValueError("Downloaded XML is not an SVG image.")

        allowed_tags = {
            "svg", "g", "path", "rect", "circle", "ellipse",
            "line", "polyline", "polygon", "defs", "clipPath",
            "mask", "linearGradient", "radialGradient", "stop",
            "title", "desc", "style",
        }

        for element in root.iter():
            tag = element.tag.split("}")[-1]
            if tag not in allowed_tags:
                raise ValueError(f"Unsupported SVG element: {tag}")

            for attribute, value in element.attrib.items():
                attribute = attribute.split("}")[-1].lower()
                if attribute.startswith("on") or attribute in {
                    "href", "src", "base"
                }:
                    raise ValueError("SVG contains an unsupported reference.")

                if "url(" in value.lower():
                    raise ValueError("SVG URL references need separate review.")

            if tag == "style":
                css = (element.text or "").lower()
                if any(token in css for token in (
                    "url(", "@import", "\\", "/*", "expression("
                )):
                    raise ValueError("SVG stylesheet needs separate review.")

        path = LOGO_FOLDER / f"{company_id}_{digest}.svg"
        path.write_bytes(content)
        return path

    with Image.open(io.BytesIO(content)) as image:
        width, height = image.size
        if min(width, height) < 16 or width * height > 4_000_000:
            raise ValueError("Unsuitable image dimensions.")

        image.load()
        image = image.convert("RGBA")
        image.thumbnail((600, 600))

        path = LOGO_FOLDER / f"{company_id}_{digest}.png"
        image.save(path, "PNG")

    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("symbols", nargs="+")
    args = parser.parse_args()

    if not DB_PATH.exists():
        raise FileNotFoundError("Database missing.")

    LOGO_FOLDER.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        with requests.Session() as session:
            for symbol in dict.fromkeys(s.upper() for s in args.symbols):
                company = connection.execute("""
                    SELECT c.id, c.official_website,
                           l.local_path, l.manual_override, l.status
                    FROM companies c
                    LEFT JOIN company_logos l ON l.company_id = c.id
                    WHERE c.exchange = 'PSX' AND c.symbol = ?
                """, (symbol,)).fetchone()

                if not company or not company["official_website"]:
                    print(f"{symbol}: company website missing.")
                    continue

                if company["manual_override"] or company["status"] == "reviewed":
                    print(f"{symbol}: reviewed/manual logo preserved.")
                    continue

                if company["local_path"]:
                    if (ROOT / company["local_path"]).exists():
                        print(f"{symbol}: cached logo exists; review it first.")
                        continue

                website = company["official_website"]
                # Prefer HTTPS; do not fall back to unencrypted HTTP.
                if website.startswith("http://"):
                    website = "https://" + website[len("http://"):]

                status = "failed"
                error = None
                logo_url = None
                local_path = None

                try:
                    html, final_url = download(session, website)
                    candidates = find_candidates(html, final_url)
                    print(f"{symbol}: {len(candidates)} logo candidates")

                    if not candidates:
                        status = "not_found"
                        error = "No logo-labelled image found."

                    for candidate in candidates[:5]:
                        try:
                            content, resolved_url = download(session, candidate)
                            path = save_image(content, company["id"])
                            logo_url = resolved_url
                            local_path = path.relative_to(ROOT).as_posix()
                            status = "downloaded"
                            error = None
                            break
                        except (
                            requests.RequestException,
                            OSError,
                            ValueError,
                            Image.DecompressionBombError,
                        ) as exc:
                            error = str(exc)
                            print(f"  Candidate skipped: {candidate} | {exc}")

                            if isinstance(exc, requests.HTTPError):
                                if exc.response.status_code in {403, 429}:
                                    break

                except (requests.RequestException, ValueError) as exc:
                    error = str(exc)

                with connection:
                    connection.execute("""
                        INSERT INTO company_logos (
                            company_id, source_url, local_path,
                            status, checked_at, last_error
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(company_id) DO UPDATE SET
                            source_url = excluded.source_url,
                            local_path = excluded.local_path,
                            status = excluded.status,
                            checked_at = excluded.checked_at,
                            last_error = excluded.last_error
                    """, (
                        company["id"], logo_url, local_path, status,
                        datetime.now(timezone.utc).isoformat(), error,
                    ))

                print(f"{symbol}: {status}")
                print(f"  {local_path or error}")


if __name__ == "__main__":
    main()