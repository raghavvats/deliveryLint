"""Regression tests for the Northstar Components synthetic case.

These tests pin the classification behavior that the prioritized claim
classifier is meant to guarantee:

* explicit exclusions become contradictions / out-of-scope violations rather
  than generic "unsupported" findings,
* date and responsibility conflicts are detected,
* vague language is flagged,
* and legitimate in-scope CPQ items are NOT broadly flagged as unsupported.

The structured fixtures deliberately give target claims and reference facts
*different* normalized subjects, so passing these tests proves the engine matches
by meaning rather than exact string equality.
"""

import asyncio

import pytest

from backend.app.schemas.correction_ui import CorrectionFindingView
from backend.app.schemas.enums import LintFindingType, LintSeverity, ReviewPriority
from backend.app.pipeline.run_pipeline import run_custom_pipeline
from tests.fixtures.northstar_pipeline import (
    build_northstar_mock_client,
    build_northstar_request,
)

CONTRADICTION_LIKE = {
    LintFindingType.REFERENCE_CONTRADICTION,
    LintFindingType.STATUS_AUTHORITY_MISMATCH,
}


@pytest.fixture(scope="module")
def northstar_findings() -> list[CorrectionFindingView]:
    result = asyncio.run(
        run_custom_pipeline(
            build_northstar_request(),
            llm_client=build_northstar_mock_client(),
        )
    )
    return result.correction_ui_response.findings


def _by_quote(findings: list[CorrectionFindingView], fragment: str) -> list[CorrectionFindingView]:
    fragment = fragment.lower()
    return [
        f for f in findings if f.target_quote and fragment in f.target_quote.lower()
    ]


def test_netsuite_billing_sync_is_contradiction_not_merely_unsupported(northstar_findings) -> None:
    matches = _by_quote(northstar_findings, "NetSuite billing sync for approved quotes")
    assert matches, "Expected a finding for the NetSuite billing sync scope claim"
    types = {f.finding_type for f in matches}
    assert types & CONTRADICTION_LIKE, (
        "NetSuite billing sync should be a contradiction / out-of-scope violation, "
        f"got {types}"
    )
    assert LintFindingType.UNSUPPORTED_TARGET_CLAIM not in types
    assert any(f.priority == ReviewPriority.NEEDS_FIX for f in matches)
    assert any(f.severity in {LintSeverity.HIGH, LintSeverity.CRITICAL} for f in matches)


def test_customer_portal_quote_acceptance_flagged_against_exclusions(northstar_findings) -> None:
    matches = _by_quote(
        northstar_findings, "Customer portal quote acceptance so distributors"
    )
    assert matches
    types = {f.finding_type for f in matches}
    assert LintFindingType.REFERENCE_CONTRADICTION in types
    assert LintFindingType.UNSUPPORTED_TARGET_CLAIM not in types
    assert any(f.priority == ReviewPriority.NEEDS_FIX for f in matches)


def test_customer_portal_prototype_deliverable_flagged_against_exclusions(northstar_findings) -> None:
    matches = _by_quote(northstar_findings, "Customer portal quote acceptance prototype")
    assert matches
    assert LintFindingType.REFERENCE_CONTRADICTION in {f.finding_type for f in matches}


def test_netsuite_billing_integration_design_deliverable_flagged(northstar_findings) -> None:
    matches = _by_quote(northstar_findings, "NetSuite billing integration design")
    assert matches, "Expected a finding for the NetSuite billing integration design deliverable"
    assert LintFindingType.REFERENCE_CONTRADICTION in {f.finding_type for f in matches}
    assert any(f.priority == ReviewPriority.NEEDS_FIX for f in matches)


def test_weak_change_control_flagged(northstar_findings) -> None:
    matches = _by_quote(northstar_findings, "active sprint backlog with agreement")
    assert matches, "Expected a finding for weak change-control language"
    contradiction = [
        f for f in matches if f.finding_type == LintFindingType.REFERENCE_CONTRADICTION
    ]
    assert contradiction, "Weak change control should contradict the signed change-control rule"
    assert any(f.rule_id == "contradiction.change_control_weakened" for f in contradiction)
    assert any(f.priority == ReviewPriority.NEEDS_FIX for f in contradiction)


def test_go_live_date_conflict_detected(northstar_findings) -> None:
    matches = _by_quote(northstar_findings, "production go-live targeted for August 15")
    assert matches
    contradiction = [
        f for f in matches if f.finding_type == LintFindingType.REFERENCE_CONTRADICTION
    ]
    assert contradiction, "August 15 vs August 1 go-live should be a contradiction"
    # The reference evidence should cite the authoritative August 1 date.
    assert any(
        any("august 1" in q.lower() for q in f.reference_quotes) for f in contradiction
    )
    assert any(f.priority == ReviewPriority.NEEDS_FIX for f in contradiction)


def test_auctor_owned_uat_execution_is_responsibility_conflict(northstar_findings) -> None:
    matches = _by_quote(northstar_findings, "Define and execute all UAT test scripts")
    assert matches
    contradiction = [
        f for f in matches if f.finding_type == LintFindingType.REFERENCE_CONTRADICTION
    ]
    assert contradiction
    assert any(f.rule_id == "contradiction.responsibility_conflict" for f in contradiction)


def test_netsuite_credentials_dependency_flagged(northstar_findings) -> None:
    matches = _by_quote(northstar_findings, "NetSuite sandbox access and API credentials")
    assert matches
    assert LintFindingType.REFERENCE_CONTRADICTION in {f.finding_type for f in matches}


def test_vague_language_flagged(northstar_findings) -> None:
    matches = _by_quote(northstar_findings, "fast, user-friendly, and seamless")
    assert matches
    assert LintFindingType.VAGUE_REQUIREMENT in {f.finding_type for f in matches}


@pytest.mark.parametrize(
    "fragment",
    [
        "Product catalog setup for approximately 850",
        "Price book configuration for list pricing",
        "Quote PDFs are generated using the approved",
        "Discount approval workflow for non-standard",
        "identify UAT participants",
    ],
)
def test_legitimate_scope_items_not_flagged_unsupported(northstar_findings, fragment) -> None:
    matches = _by_quote(northstar_findings, fragment)
    flagged_types = {f.finding_type for f in matches}
    assert LintFindingType.UNSUPPORTED_TARGET_CLAIM not in flagged_types, (
        f"Legitimate in-scope item '{fragment}' was incorrectly flagged unsupported "
        f"(findings: {flagged_types})"
    )


def test_unsupported_is_never_needs_fix(northstar_findings) -> None:
    """unsupported_target_claim is a fallback; it must never be a blocking finding."""
    for finding in northstar_findings:
        if finding.finding_type == LintFindingType.UNSUPPORTED_TARGET_CLAIM:
            assert finding.priority != ReviewPriority.NEEDS_FIX


@pytest.mark.parametrize(
    "fragment",
    [
        "NetSuite billing sync for approved quotes",
        "NetSuite billing integration design",
        "Customer portal quote acceptance so distributors",
        "Customer portal quote acceptance prototype",
        "Define and execute all UAT test scripts",
        "active sprint backlog with agreement",
    ],
)
def test_explicit_exclusion_and_responsibility_snippets_are_contradictions(
    northstar_findings, fragment
) -> None:
    """Each previously-missed snippet must produce a blocking contradiction.

    These pass even though the fixtures emulate realistic extraction noise
    (out-of-scope facts not labelled NEGATIVE, UAT owners not extracted as
    attributes), proving recall does not depend on those fragile signals.
    """
    matches = _by_quote(northstar_findings, fragment)
    assert matches, f"Expected a finding for '{fragment}'"
    types = {f.finding_type for f in matches}
    assert LintFindingType.REFERENCE_CONTRADICTION in types, (
        f"'{fragment}' should be a contradiction, got {types}"
    )
    assert LintFindingType.UNSUPPORTED_TARGET_CLAIM not in types, (
        f"'{fragment}' should not be a bare unsupported finding"
    )
    assert any(f.priority == ReviewPriority.NEEDS_FIX for f in matches)


def test_seeded_issues_produce_blocking_findings(northstar_findings) -> None:
    needs_fix = [f for f in northstar_findings if f.priority == ReviewPriority.NEEDS_FIX]
    # NetSuite sync/design/credentials, both portal items, the date, and UAT ownership.
    assert len(needs_fix) >= 6
    assert all(
        f.finding_type != LintFindingType.UNSUPPORTED_TARGET_CLAIM for f in needs_fix
    )


# --- Precision / false-positive regressions ---------------------------------


def test_sales_cloud_integration_not_matched_to_netsuite_exclusion(northstar_findings) -> None:
    """Sharing only the generic word "integration" must not trigger an exclusion."""
    matches = _by_quote(northstar_findings, "Salesforce Sales Cloud objects including Account")
    assert LintFindingType.REFERENCE_CONTRADICTION not in {f.finding_type for f in matches}
    assert all(
        f.rule_id != "contradiction.target_includes_excluded_item" for f in matches
    )


def test_out_of_scope_redesign_not_contradiction(northstar_findings) -> None:
    """An item under the Out-of-Scope heading must keep exclusion polarity."""
    matches = _by_quote(northstar_findings, "Major redesign of Sales Cloud opportunity management")
    assert LintFindingType.REFERENCE_CONTRADICTION not in {f.finding_type for f in matches}


def test_admin_access_not_responsibility_conflict(northstar_findings) -> None:
    """Auctor's admin-access responsibility is unrelated to project governance."""
    matches = _by_quote(
        northstar_findings, "have access to a Northstar Salesforce system administrator"
    )
    assert all(
        f.rule_id != "contradiction.responsibility_conflict" for f in matches
    )


@pytest.mark.parametrize(
    "fragment",
    [
        "Auctor Systems will lead discovery validation",
        "Northstar will provide project sponsorship",
    ],
)
def test_explicit_owner_sentences_not_missing_owner(northstar_findings, fragment) -> None:
    matches = _by_quote(northstar_findings, fragment)
    assert LintFindingType.MISSING_OWNER not in {f.finding_type for f in matches}


def test_no_duplicate_unsupported_or_unresolved_for_strongly_flagged_claim(
    northstar_findings,
) -> None:
    """A claim with a contradiction must not also carry unsupported/unresolved."""
    by_claim: dict[str, set[LintFindingType]] = {}
    for finding in northstar_findings:
        # CorrectionFindingView lacks claim id, so group by target quote instead.
        if finding.target_quote is None:
            continue
        by_claim.setdefault(finding.target_quote, set()).add(finding.finding_type)

    weak = {
        LintFindingType.UNSUPPORTED_TARGET_CLAIM,
        LintFindingType.UNRESOLVED_REFERENCE_CONFLICT,
    }
    for types in by_claim.values():
        if LintFindingType.REFERENCE_CONTRADICTION in types or (
            LintFindingType.STATUS_AUTHORITY_MISMATCH in types
        ):
            assert not (types & weak)
