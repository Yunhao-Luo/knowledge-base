from __future__ import annotations

from collections import Counter
from math import log
from pathlib import Path
import re


TOKEN_RE = re.compile(r"[a-z0-9]{2,}")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def rank_files(query: str, pages: dict[Path, str], limit: int) -> list[Path]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return list(pages)[:limit]
    doc_tokens = {path: tokenize(text) for path, text in pages.items()}
    doc_freq = Counter()
    for tokens in doc_tokens.values():
        for token in set(tokens):
            doc_freq[token] += 1
    total_docs = max(len(doc_tokens), 1)
    scores: list[tuple[float, Path]] = []
    for path, tokens in doc_tokens.items():
        counts = Counter(tokens)
        score = 0.0
        for token in query_tokens:
            if counts[token] == 0:
                continue
            idf = log((1 + total_docs) / (1 + doc_freq[token])) + 1.0
            score += counts[token] * idf
        if score > 0:
            scores.append((score, path))
    scores.sort(reverse=True)
    return [path for _, path in scores[:limit]]
