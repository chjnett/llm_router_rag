from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable


TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


def bm25_rank(query: str, documents: list[str], k1: float = 1.2, b: float = 0.75) -> list[int]:
    tokenized = [tokenize(document) for document in documents]
    query_terms = set(tokenize(query))
    n_docs = len(tokenized)
    average_length = sum(map(len, tokenized)) / n_docs if n_docs else 0.0
    document_frequency = Counter(term for terms in tokenized for term in set(terms))
    scores: list[tuple[float, int]] = []
    for index, terms in enumerate(tokenized):
        frequencies = Counter(terms)
        score = 0.0
        for term in query_terms:
            frequency = frequencies[term]
            if not frequency:
                continue
            inverse_frequency = math.log(1 + (n_docs - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            norm = frequency + k1 * (1 - b + b * len(terms) / average_length) if average_length else frequency
            score += inverse_frequency * frequency * (k1 + 1) / norm
        scores.append((score, index))
    return [index for _, index in sorted(scores, key=lambda row: (-row[0], row[1]))]


def retrieval_metrics(ranking: Iterable[int], relevant: set[int], cutoffs: tuple[int, ...] = (1, 5, 10)) -> dict[str, float]:
    ranked = list(ranking)
    result = {
        f"recall_at_{cutoff}": len(set(ranked[:cutoff]) & relevant) / len(relevant) if relevant else 0.0
        for cutoff in cutoffs
    }
    first = next((rank + 1 for rank, index in enumerate(ranked) if index in relevant), None)
    result["mrr"] = 1.0 / first if first else 0.0
    gains = [1.0 if index in relevant else 0.0 for index in ranked[:5]]
    dcg = sum(gain / math.log2(rank + 2) for rank, gain in enumerate(gains))
    ideal = sum(1.0 / math.log2(rank + 2) for rank in range(min(5, len(relevant))))
    result["ndcg_at_5"] = dcg / ideal if ideal else 0.0
    return result


def mean_metrics(rows: list[dict[str, float]]) -> dict[str, float]:
    return {key: sum(row[key] for row in rows) / len(rows) for key in rows[0]} if rows else {}
