from backend.app.domain.span_resolution import resolve_char_span, resolve_evidence_span, resolve_target_location
from backend.app.schemas.project_fact import EvidenceSpan
from backend.app.schemas.target_document import TargetLocation


def test_resolve_char_span_from_quote() -> None:
    text = "Production go-live: August 1, 2026 remains official."
    span = resolve_char_span(text, quote="August 1, 2026")
    assert span is not None
    assert text[span[0] : span[1]] == "August 1, 2026"


def test_resolve_target_location_fills_offsets() -> None:
    text = "Alpha beta gamma"
    location = TargetLocation(quote="beta")
    resolved = resolve_target_location(text, location)
    assert resolved is not None
    assert resolved.char_start == 6
    assert resolved.char_end == 10


def test_resolve_evidence_span_from_line_numbers() -> None:
    text = "line one\nline two\nline three"
    evidence = EvidenceSpan(quote="missing", line_start=2, line_end=2)
    resolved = resolve_evidence_span(text, evidence)
    assert resolved.char_start == 9
    assert "line two" in text[resolved.char_start : resolved.char_end]


def test_resolve_char_span_from_loose_whitespace_quote() -> None:
    text = "Official go-live:\nAugust 1, 2026."
    span = resolve_char_span(text, quote="Official go-live: August 1, 2026")
    assert span is not None
    assert text[span[0] : span[1]].startswith("Official")
