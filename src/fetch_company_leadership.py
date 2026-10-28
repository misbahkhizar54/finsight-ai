"""Collect published board/leadership cards; retain evidence for review.
Run: python src/fetch_company_leadership.py SYS ABL EFERT
No person names are hardcoded. Website layouts may need parser adjustments.
"""
import argparse
from html.parser import HTMLParser
import hashlib
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/finsight.db'
# Verified official page locations, not hardcoded people.
SOURCES = {
    'SYS': [('board', 'https://www.systemsltd.com/governance'),
            ('management', 'https://www.systemsltd.com/company-overview')],
    'ABL': [('board', 'https://www.abl.com/the-bank/company-information/board-of-directors/'),
            ('management', 'https://www.abl.com/the-bank/company-information/the-management/')],
    'EFERT': [('board', 'https://www.engrofertilizers.com/progress#b-o-d/'),
            ('management', 'https://www.engrofertilizers.com/progress#leadership/')]
}
ROLE = re.compile(r'\b(director|chairman|chairperson|chairwoman|chief|CEO|CFO|COO|CHRO|CTO|CIO|president|secretary|head|manager|SVP|EVP)\b', re.I)
HEADING = re.compile(r'^h[1-6]$')


def clean(text):
    return ' '.join(text.split())


class SystemsBoardParser(HTMLParser):
    """Only read name/title fields in cards inside directors-section."""
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
            'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.section_depth = None
        self.card_depth = None
        self.info_depth = None
        self.field_depth = None
        self.field = None
        self.card = None
        self.people = []
        self.section_found = False
        self.card_count = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        attrs = dict(attrs)
        self.stack.append(tag)
        depth = len(self.stack)
        classes = attrs.get('class', '').split()
        if attrs.get('id') == 'directors-section':
            self.section_depth = depth
            self.section_found = True
        if self.section_depth and 'leadership-box' in classes:
            self.card_depth = depth
            self.card = {'name': '', 'role': '', 'category': 'board'}
            self.card_count += 1
        if self.card_depth and 'leadership-info' in classes:
            self.info_depth = depth
        if self.info_depth and tag in {'h5', 'p'}:
            self.field = 'name' if tag == 'h5' else 'role'
            self.field_depth = depth

    def handle_data(self, value):
        if self.field and self.card is not None:
            self.card[self.field] += value

    def handle_endtag(self, tag):
        if tag not in self.stack:
            return
        while self.stack:
            depth = len(self.stack)
            ended = self.stack.pop()
            if depth == self.field_depth:
                self.field = self.field_depth = None
            if depth == self.info_depth:
                self.info_depth = None
            if depth == self.card_depth:
                person = self.card
                person['name'] = clean(person['name'])
                person['role'] = clean(person['role'])
                if person['name'] and person['role'] and ROLE.search(person['role']):
                    person['evidence'] = person['name'] + ' | ' + person['role']
                    self.people.append(person)
                self.card = self.card_depth = None
            if depth == self.section_depth:
                self.section_depth = None
            if ended == tag:
                break


def parse_systems_board(html):
    parser = SystemsBoardParser()
    parser.feed(html.decode('utf-8', errors='replace') if isinstance(html, bytes) else html)
    parser.close()
    if not parser.section_found or not parser.card_count:
        raise ValueError('Systems board section/cards missing; source layout needs review.')
    if len(parser.people) != parser.card_count:
        raise ValueError('A Systems board card has missing/invalid fields; review saved HTML.')
    return list({(p['name'].casefold(), p['role'].casefold()): p for p in parser.people}.values())


def parse_people(html, category, source_url=""):
    """Extract adjacent name/title cards, never biography sentences.

    Output remains candidate evidence until reviewed. No claim of full coverage.
    """
    # Fail closed for the Systems board page; never fall back to whole-page headings.
    if category == 'board' and (urlparse(source_url).hostname or '').removeprefix('www.') == 'systemsltd.com':
        return parse_systems_board(html)
    soup = BeautifulSoup(html, 'html.parser')
    for node in soup.select('script,style,nav,footer,header'):
        node.decompose()
    people, seen = [], set()
    for heading in soup.find_all(HEADING):
        name = clean(heading.get_text(' ', strip=True))
        if not 2 <= len(name.split()) <= 7 or len(name) > 90:
            continue
        if ROLE.search(name) or re.search(r'\d|[!?@:/]', name):
            continue
        if re.search(r'\b(our|about|contact|leadership|management|committee|company|bank|systems|governance|profile)\b', name, re.I):
            continue
        # Stop at the next heading. Long paragraphs are biographies, not titles.
        role = None
        for element in heading.next_elements:
            if getattr(element, 'name', None) and HEADING.match(element.name):
                title = clean(element.get_text(' ', strip=True))
                if len(title) <= 150 and len(title.split()) <= 20 and ROLE.search(title):
                    role = title
                break
            if getattr(element, 'name', None) in {'p', 'span', 'div'}:
                text = clean(element.get_text(' ', strip=True))
                if not text or text == name:
                    continue
                if len(text) > 150 or len(text.split()) > 20:
                    break
                if ROLE.search(text) and not re.search(r'\b(served|joined|previously|experience|years|has been)\b', text, re.I):
                    role = text
                    break
        if not role:
            continue
        key = (name.casefold(), role.casefold())
        if key in seen:
            continue
        seen.add(key)
        group = category
        if category == 'mixed':
            group = 'board' if re.search(r'\b(director|chairman|chairperson)\b', role, re.I) else 'management'
        people.append({'name': name, 'role': role, 'category': group,
                       'evidence': name + ' | ' + role})
    return people


def init_db(con):
    con.execute('''CREATE TABLE IF NOT EXISTS leadership_fetches (
        id INTEGER PRIMARY KEY, company_id INTEGER NOT NULL REFERENCES companies(id),
        category TEXT NOT NULL, source_url TEXT NOT NULL, fetched_at TEXT NOT NULL,
        raw_path TEXT, sha256 TEXT, status TEXT NOT NULL, error TEXT,
        people_json TEXT NOT NULL, source_as_of TEXT,
        UNIQUE(company_id,source_url,fetched_at))''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('symbols', nargs='+')
    parser.add_argument('--html', type=Path, help='Parse a locally saved source HTML file (one symbol and --url required).')
    parser.add_argument('--url', help='Official source URL for --html or an additional company source.')
    parser.add_argument('--category', choices=['board', 'management', 'mixed'], default='mixed')
    args = parser.parse_args()
    symbols = list(dict.fromkeys(s.upper() for s in args.symbols))
    if args.url and len(symbols) != 1:
        parser.error('--url requires exactly one symbol')
    if args.html and not args.url:
        parser.error('--html requires --url')
    if not DB.exists():
        raise SystemExit('Database missing. Run from your installed project.')
    folder = ROOT / 'data/raw/company_leadership'
    folder.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as con, requests.Session() as session:
        con.execute('PRAGMA foreign_keys=ON')
        init_db(con)
        for symbol in symbols:
            company = con.execute("SELECT id,official_website FROM companies WHERE exchange='PSX' AND symbol=?", (symbol,)).fetchone()
            if not company:
                print(f'{symbol}: import its PSX profile first.'); continue
            sources = [(args.category, args.url)] if args.url else SOURCES.get(symbol, [])
            if not sources:
                print(f'{symbol}: source not configured. Use --url OFFICIAL_PAGE --category board or management.'); continue
            for category, url in sources:
                official_host = (urlparse(company[1] or '').hostname or '').removeprefix('www.')
                host = (urlparse(url).hostname or '').removeprefix('www.')
                if urlparse(url).scheme != 'https' or not official_host or host != official_host:
                    print(f'{symbol}: skipped URL outside registered official HTTPS domain.'); continue
                stamp = datetime.now(timezone.utc).isoformat()
                raw_path = None; digest = None; people = []; error = None
                blocked = False
                try:
                    if args.html:
                        content = args.html.read_bytes()
                    else:
                        with session.get(url, timeout=(10, 45), stream=True) as response:
                            if response.status_code in (403, 429):
                                blocked = True
                            response.raise_for_status()
                            if (urlparse(response.url).hostname or '').removeprefix('www.') != host:
                                raise ValueError('Redirect outside registered domain')
                            chunks=[]; size=0
                            for chunk in response.iter_content(65536):
                                size += len(chunk)
                                if size > 5_000_000:
                                    raise ValueError('HTML exceeds 5 MB')
                                chunks.append(chunk)
                            content=b''.join(chunks)
                    digest = hashlib.sha256(content).hexdigest()
                    raw = folder / f'{symbol}_{category}_{digest[:16]}.html'
                    raw.write_bytes(content)
                    raw_path = raw.relative_to(ROOT).as_posix()
                    people = parse_people(content, category, url)
                    status = 'needs_review' if people else 'no_matches'
                except (requests.RequestException, OSError, ValueError) as exc:
                    status='failed'; error=str(exc)
                with con:
                    con.execute('''INSERT INTO leadership_fetches
                        (company_id,category,source_url,fetched_at,raw_path,sha256,status,error,people_json)
                        VALUES (?,?,?,?,?,?,?,?,?)''',
                        (company[0],category,url,stamp,raw_path,digest,status,error,json.dumps(people,ensure_ascii=False)))
                print(f'{symbol} | {category}: {len(people)} candidates | {status}')
                for person in people:
                    print(f"  {person['name']} | {person['role']}")
                if error: print(f'  {error}')
                if raw_path: print(f'  Evidence: {raw_path}')
                if blocked:
                    print('Access/rate limit received; stopping batch.'); return
                if not args.html: time.sleep(2)
    print('Saved source observations. Candidate rows need review; missing rows do not establish resignations.')


if __name__ == '__main__':
    main()
