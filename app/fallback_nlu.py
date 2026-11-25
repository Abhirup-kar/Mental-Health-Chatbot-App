"""Lightweight local NLU fallback trained from rasa_bot/data/nlu.yml when Rasa server is offline."""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


class LocalNLUFallback:
    """TF-IDF cosine-similarity intent matcher backed by Rasa's own NLU examples."""

    def __init__(self, nlu_path: Path | None = None) -> None:
        if nlu_path is None:
            nlu_path = Path(__file__).resolve().parent.parent / "rasa_bot" / "data" / "nlu.yml"
        self.examples: list[tuple[str, Counter[str]]] = []
        self.idf: dict[str, float] = {}
        self._load_nlu(nlu_path)

    def _load_nlu(self, nlu_path: Path) -> None:
        if not nlu_path.exists():
            return
        with nlu_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        raw_examples: list[tuple[str, list[str]]] = []
        doc_freq: Counter[str] = Counter()
        for entry in data.get("nlu", []):
            intent = entry.get("intent")
            examples_block = entry.get("examples", "")
            if not intent or not examples_block:
                continue
            for line in str(examples_block).splitlines():
                cleaned = line.strip()
                if cleaned.startswith("- "):
                    utterance = cleaned[2:].strip()
                    tokens = _tokenize(utterance)
                    if tokens:
                        raw_examples.append((intent, tokens))
                        doc_freq.update(set(tokens))

        num_docs = max(1, len(raw_examples))
        self.idf = {
            token: math.log((num_docs + 1) / (df + 1)) + 1.0
            for token, df in doc_freq.items()
        }
        self.examples = [(intent, Counter(tokens)) for intent, tokens in raw_examples]

    def _tfidf(self, counts: Counter[str]) -> dict[str, float]:
        return {tok: cnt * self.idf.get(tok, 1.0) for tok, cnt in counts.items()}

    def parse(self, text: str) -> dict[str, Any]:
        tokens = _tokenize(text)
        if not tokens or not self.examples:
            return {"name": "nlu_fallback", "confidence": 0.0}

        query_vec = self._tfidf(Counter(tokens))
        query_norm = math.sqrt(sum(v * v for v in query_vec.values())) or 1.0

        best_intent = "nlu_fallback"
        best_score = 0.0
        for intent, counts in self.examples:
            ex_vec = self._tfidf(counts)
            ex_norm = math.sqrt(sum(v * v for v in ex_vec.values())) or 1.0
            dot = sum(query_vec[t] * ex_vec[t] for t in query_vec if t in ex_vec)
            sim = dot / (query_norm * ex_norm)
            if sim > best_score:
                best_score = sim
                best_intent = intent

        if best_score < 0.25:
            return {"name": "nlu_fallback", "confidence": round(best_score, 4)}
        return {"name": best_intent, "confidence": round(min(0.95, best_score), 4)}
