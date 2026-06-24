"""Tests for DeliveryLint benchmark suite loading and scoring."""

from backend.app.schemas.correction_ui import CorrectionFindingView
from backend.app.schemas.enums import DocType, LintFindingType, LintSeverity, ReviewPriority
from backend.app.test_harness.scorer import score_expected_findings
from backend.app.test_harness.suite_loader import discover_suites, parse_answer_key


def test_discover_all_five_suites() -> None:
    suites = discover_suites()
    assert len(suites) == 5
    ids = {suite.id for suite in suites}
    assert "deliverylint_suite_01_cpq_sow_scope_drift" in ids
    assert "deliverylint_suite_05_wms_change_order_authority_and_completeness" in ids


def test_suite_01_answer_key_parsing() -> None:
    suite = next(s for s in discover_suites() if s.id.endswith("suite_01_cpq_sow_scope_drift"))
    assert suite.target_filename == "target_draft_sow.md"
    assert suite.target_doc_type == DocType.DRAFT_SOW
    assert len(suite.expected_findings) == 14
    assert suite.expected_findings[0].acceptable_types == [LintFindingType.REFERENCE_CONTRADICTION]


def test_answer_key_parses_alternative_finding_types() -> None:
    text = (
        "## Injected Findings\n\n"
        "5. `unresolved_reference_conflict` or `status_authority_mismatch` — Example description.\n"
    )
    _, _, findings = parse_answer_key(text)
    assert len(findings) == 1
    assert findings[0].acceptable_types == [
        LintFindingType.UNRESOLVED_REFERENCE_CONFLICT,
        LintFindingType.STATUS_AUTHORITY_MISMATCH,
    ]


def test_scorer_matches_by_type_and_keywords() -> None:
    expected = discover_suites()[0].expected_findings[0]
    actual = [
        CorrectionFindingView(
            id="f1",
            priority=ReviewPriority.NEEDS_FIX,
            finding_type=LintFindingType.REFERENCE_CONTRADICTION,
            severity=LintSeverity.HIGH,
            confidence=0.9,
            title="Accessories not in signed SOW scope",
            message="Signed SOW limits guided selling to Treadmills, Bikes, and Rowers.",
            rule_id="rule",
        )
    ]
    results, extra = score_expected_findings([expected], actual)
    assert results[0].caught is True
    assert extra == []


def test_scorer_allows_one_finding_to_match_multiple_expected_items() -> None:
    expected_a = discover_suites()[0].expected_findings[7]
    expected_b = discover_suites()[0].expected_findings[8]
    actual = [
        CorrectionFindingView(
            id="f1",
            priority=ReviewPriority.NEEDS_FIX,
            finding_type=LintFindingType.REFERENCE_CONTRADICTION,
            severity=LintSeverity.HIGH,
            confidence=0.9,
            title="Responsibility for UAT execution and production credentials conflicts",
            message=(
                "Target assigns Auctor owns UAT execution, price book cleanup, and "
                "production credentials, but signed SOW says Nimbus owns UAT execution "
                "and final price book export."
            ),
            target_quote="Auctor will own configuration, UAT execution, price book cleanup, and production credentials.",
            rule_id="rule",
        )
    ]
    results, _ = score_expected_findings([expected_a, expected_b], actual)
    assert results[0].caught is True
    assert results[1].caught is True
