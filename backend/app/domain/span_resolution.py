"""Resolve character spans from quote or line hints when offsets are missing."""

import re

from backend.app.schemas.project_fact import EvidenceSpan
from backend.app.schemas.target_document import TargetLocation

_WORD_CHAR = re.compile(r"[\w'-]", re.UNICODE)


def _is_word_char(char: str) -> bool:
    return bool(_WORD_CHAR.match(char))


def _expand_to_word_boundaries(text: str, start: int, end: int) -> tuple[int, int]:
    while start > 0 and _is_word_char(text[start - 1]):
        start -= 1
    while end < len(text) and _is_word_char(text[end]):
        end += 1
    return start, end


def _normalize_quote_for_match(quote: str) -> str:
    normalized = quote.strip().lower()
    normalized = normalized.replace("\u2018", "'").replace("\u2019", "'")
    normalized = normalized.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", normalized)


def _find_quote_span_loose(text: str, quote: str) -> tuple[int, int] | None:
    trimmed = quote.strip()
    if not trimmed:
        return None

    words = re.split(r"\s+", trimmed)
    if len(words) < 2:
        return None

    pattern = r"\s+".join(re.escape(word) for word in words)
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if match is None:
        return None
    return _expand_to_word_boundaries(text, match.start(), match.end())


def _find_quote_span(text: str, quote: str) -> tuple[int, int] | None:
    trimmed = quote.strip()
    if not trimmed:
        return None
    index = text.find(trimmed)
    if index >= 0:
        return _expand_to_word_boundaries(text, index, index + len(trimmed))

    loose = _find_quote_span_loose(text, trimmed)
    if loose is not None:
        return loose

    normalized_quote = _normalize_quote_for_match(trimmed)
    if len(normalized_quote) < 12:
        return None

    window = len(normalized_quote)
    step = max(1, window // 4)
    for start in range(0, max(1, len(text) - window + 1), step):
        chunk = text[start : start + window + 40]
        if _normalize_quote_for_match(chunk[:window]) == normalized_quote:
            return _expand_to_word_boundaries(text, start, start + len(trimmed))
        if normalized_quote in _normalize_quote_for_match(chunk):
            local = _normalize_quote_for_match(chunk).index(normalized_quote)
            span_start = start + local
            return _expand_to_word_boundaries(text, span_start, span_start + len(trimmed))

    return None


def _line_span(text: str, line_start: int, line_end: int | None) -> tuple[int, int] | None:
    lines = text.splitlines(keepends=True)
    if line_start < 1 or line_start > len(lines):
        return None
    end_line = line_end if line_end is not None else line_start
    if end_line < line_start:
        end_line = line_start
    char_start = sum(len(lines[i]) for i in range(line_start - 1))
    char_end = sum(len(lines[i]) for i in range(end_line))
    return _expand_to_word_boundaries(text, char_start, char_end)


def resolve_char_span(
    text: str,
    *,
    char_start: int | None = None,
    char_end: int | None = None,
    quote: str | None = None,
    line_start: int | None = None,
    line_end: int | None = None,
) -> tuple[int, int] | None:
    if quote:
        found = _find_quote_span(text, quote)
        if found is not None:
            return found

    if char_start is not None and char_end is not None and char_end > char_start:
        return _expand_to_word_boundaries(text, char_start, char_end)

    if line_start is not None:
        return _line_span(text, line_start, line_end)

    return None


def resolve_target_location(text: str, location: TargetLocation | None) -> TargetLocation | None:
    if location is None:
        return None
    span = resolve_char_span(
        text,
        char_start=location.char_start,
        char_end=location.char_end,
        quote=location.quote,
        line_start=location.line_start,
        line_end=location.line_end,
    )
    if span is None:
        return location
    char_start, char_end = span
    return location.model_copy(update={"char_start": char_start, "char_end": char_end})


def resolve_evidence_span(text: str, evidence: EvidenceSpan) -> EvidenceSpan:
    span = resolve_char_span(
        text,
        char_start=evidence.char_start,
        char_end=evidence.char_end,
        quote=evidence.quote,
        line_start=evidence.line_start,
        line_end=evidence.line_end,
    )
    if span is None:
        return evidence
    char_start, char_end = span
    return evidence.model_copy(update={"char_start": char_start, "char_end": char_end})
