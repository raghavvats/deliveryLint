"""Score lint output against answer-key expectations."""

from __future__ import annotations

from backend.app.schemas.correction_ui import CorrectionFindingView
from backend.app.schemas.enums import LintFindingType
from backend.app.test_harness.schemas import (
    ActualFindingSnapshot,
    ExpectedFinding,
    ExpectedFindingResult,
)
from backend.app.test_harness.suite_loader import extract_match_keywords

MATCH_THRESHOLD = 0.12
MIN_KEYWORD_OVERLAP = 2


def _finding_text(finding: CorrectionFindingView) -> str:
    parts = [finding.title, finding.message]
    if finding.target_quote:
        parts.append(finding.target_quote)
    if finding.reference_quotes:
        parts.extend(finding.reference_quotes)
    return " ".join(parts)


def _match_score(expected: ExpectedFinding, finding: CorrectionFindingView) -> float:
    if finding.finding_type not in expected.acceptable_types:
        return 0.0

    expected_keywords = extract_match_keywords(expected.description)
    actual_keywords = extract_match_keywords(_finding_text(finding))
    if not expected_keywords:
        return 0.0

    overlap = expected_keywords & actual_keywords
    if not overlap:
        return 0.0

    score = len(overlap) / len(expected_keywords)
    if len(overlap) >= MIN_KEYWORD_OVERLAP or any(char.isdigit() for char in "".join(overlap)):
        return max(score, MATCH_THRESHOLD)
    return score


def score_expected_findings(
    expected_findings: list[ExpectedFinding],
    actual_findings: list[CorrectionFindingView],
) -> tuple[list[ExpectedFindingResult], list[ActualFindingSnapshot]]:
    candidates: list[tuple[int, int, float]] = []
    for expected_index, expected in enumerate(expected_findings):
        for actual_index, finding in enumerate(actual_findings):
            score = _match_score(expected, finding)
            if score >= MATCH_THRESHOLD:
                candidates.append((score, expected_index, actual_index))

    candidates.sort(key=lambda item: item[0], reverse=True)
    matched_expected: set[int] = set()
    matched_actual: set[int] = set()
    expected_matches: dict[int, tuple[CorrectionFindingView, float]] = {}

    for score, expected_index, actual_index in candidates:
        if expected_index in matched_expected or actual_index in matched_actual:
            continue
        matched_expected.add(expected_index)
        matched_actual.add(actual_index)
        expected_matches[expected_index] = (actual_findings[actual_index], score)

    results: list[ExpectedFindingResult] = []
    for expected_index, expected in enumerate(expected_findings):
        match = expected_matches.get(expected_index)
        if match is None:
            results.append(
                ExpectedFindingResult(
                    index=expected.index,
                    acceptable_types=expected.acceptable_types,
                    description=expected.description,
                    caught=False,
                )
            )
            continue

        finding, score = match
        results.append(
            ExpectedFindingResult(
                index=expected.index,
                acceptable_types=expected.acceptable_types,
                description=expected.description,
                caught=True,
                matched_finding_id=finding.id,
                matched_finding_type=finding.finding_type,
                matched_title=finding.title,
                match_score=round(score, 3),
            )
        )

    extra_findings = [
        ActualFindingSnapshot(
            id=finding.id,
            finding_type=finding.finding_type,
            title=finding.title,
            message=finding.message,
        )
        for index, finding in enumerate(actual_findings)
        if index not in matched_actual
    ]
    return results, extra_findings


def recall_pct(caught_count: int, expected_count: int) -> float:
    if expected_count == 0:
        return 100.0
    return round((caught_count / expected_count) * 100.0, 1)


def summarize_types(results: list[ExpectedFindingResult]) -> dict[LintFindingType, dict[str, int]]:
    summary: dict[LintFindingType, dict[str, int]] = {}
    for result in results:
        primary_type = result.acceptable_types[0]
        bucket = summary.setdefault(primary_type, {"expected": 0, "caught": 0})
        bucket["expected"] += 1
        if result.caught:
            bucket["caught"] += 1
    return summary
