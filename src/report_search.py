import math
import re
from collections import Counter
from pathlib import Path
import json

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "of", "to", "in", "on", "and", "or", "for",
    "with", "by", "what", "how", "did", "does",
    "please", "show", "me", "about", "this", "that",
}


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if word not in STOPWORDS]


def search_report(file_path, query, limit=5, allowed_pages=None):
    """Rank report extracts using BM25 keyword retrieval."""
    query_terms = set(tokenize(query))
    if not query_terms:
        return []

    text = Path(file_path).read_text(encoding="utf-8")
    pages = re.findall(
        r"--- PDF page (\d+) ---\s*(.*?)(?=--- PDF page \d+ ---|\Z)",
        text,
        flags=re.DOTALL,
    )

    chunks = []

    for page_number, page_text in pages:
        if allowed_pages is not None:
            if int(page_number) not in allowed_pages:
                continue
        # Remove unreadable font identifiers from searchable text.
        has_font_errors = bool(re.search(r"\(cid:\d+\)", page_text))
        cleaned = re.sub(r"\(cid:\d+\)", " ", page_text)
        words = cleaned.split()

        # Overlapping extracts that never cross a PDF page boundary.
        for start in range(0, len(words), 140):
            excerpt = " ".join(words[start:start + 180])
            tokens = tokenize(excerpt)

            if tokens:
                chunks.append({
                    "page": int(page_number),
                    "text": excerpt,
                    "counts": Counter(tokens),
                    "length": len(tokens),
                    "font_warning": has_font_errors,
                })

    if not chunks:
        return []

    total = len(chunks)
    average_length = sum(c["length"] for c in chunks) / total
    document_frequency = {
        term: sum(term in c["counts"] for c in chunks)
        for term in query_terms
    }

    ranked = []

    for chunk in chunks:
        score = 0.0

        for term in query_terms:
            frequency = chunk["counts"].get(term, 0)
            if not frequency:
                continue

            df = document_frequency[term]
            idf = math.log(1 + (total - df + 0.5) / (df + 0.5))
            denominator = frequency + 1.5 * (
                0.25 + 0.75 * chunk["length"] / average_length
            )
            score += idf * frequency * 2.5 / denominator

        # Require every meaningful query word in the extract.
        all_words_found = all(
            term in chunk["counts"] for term in query_terms
        )

        # Match the complete phrase, allowing flexible spacing.
        phrase_words = re.findall(r"[a-z0-9]+", query.lower())
        phrase_pattern = (
            r"\b"
            + r"\s+".join(re.escape(word) for word in phrase_words)
            + r"\b"
        )

        exact_phrase = bool(
            re.search(phrase_pattern, chunk["text"], flags=re.IGNORECASE)
        )

        # Financial rows often contain a note number followed by an amount.
        amount_after_phrase = bool(
            re.search(
                phrase_pattern
                + r"\s+(?:\d{1,2}(?:\.\d+)?\s+)?"
                + r"\(?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?",
                chunk["text"],
                flags=re.IGNORECASE,
            )
        )

        if score > 0 and all_words_found:
            ranked.append({
                "page": chunk["page"],
                "text": chunk["text"],
                "score": score,
                "exact_phrase": exact_phrase,
                "amount_after_phrase": amount_after_phrase,
                "font_warning": chunk["font_warning"],
            })

    # Show the best matching extract from each distinct PDF page.
    results = []
    seen_pages = set()

    ranked.sort(
        key=lambda item: (
            item["amount_after_phrase"],
            item["exact_phrase"],
            item["score"],
        ),
        reverse=True,
    )

    for result in ranked:
        if result["page"] not in seen_pages:
            results.append(result)
            seen_pages.add(result["page"])
        if len(results) >= limit:
            break

    return results


def search_statements(file_path, query, limit=5):
    """Search complete statement halves, preserving headings and units."""
    terms = set(tokenize(query))
    if not terms or limit <= 0:
        return []

    records = json.loads(
        Path(file_path).read_text(encoding="utf-8")
    )

    phrase_words = re.findall(r"[a-z0-9]+", query.lower())
    phrase_pattern = (
        r"\b"
        + r"\s+".join(re.escape(word) for word in phrase_words)
        + r"\b"
    )

    results = []

    for record in records:
        raw_text = record["text"]
        cleaned = re.sub(r"\(cid:\d+\)", " ", raw_text)
        counts = Counter(tokenize(cleaned))

        if not all(term in counts for term in terms):
            continue

        results.append({
            "page": int(record["page"]),
            "side": record["side"],
            "scope": record["scope"],
            "text": (
                f"Scope: {record['scope']}; "
                f"PDF half: {record['side']}\n{cleaned}"
            ),
            "exact_phrase": bool(
                re.search(phrase_pattern, cleaned, re.IGNORECASE)
            ),
            "score": sum(counts[term] for term in terms),
            "font_warning": bool(
                re.search(r"\(cid:\d+\)", raw_text)
            ),
        })

    results.sort(
        key=lambda item: (
            -int(item["exact_phrase"]),
            -item["score"],
            item["page"],
            item["side"],
        )
    )

    return results[:limit]