"""Build descriptive finding titles and messages from matched claims/facts."""

from __future__ import annotations

from backend.app.schemas.project_fact import ProjectFact
from backend.app.schemas.target_document import TargetClaim


def _truncate(text: str, max_len: int = 140) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 3].rstrip() + "..."


def _subject_label(claim: TargetClaim) -> str:
    if claim.subject.strip():
        return claim.subject.strip()
    return claim.normalized_subject.replace("_", " ")


def exclusion_contradiction_copy(claim: TargetClaim, fact: ProjectFact) -> tuple[str, str]:
    subject = _subject_label(claim)
    return (
        f"Target includes {subject} contrary to reference exclusion",
        (
            f"Target treats {_truncate(claim.text, 100)} as in scope, but reference "
            f"explicitly excludes it: {_truncate(fact.evidence.quote, 120)}"
        ),
    )


def date_conflict_copy(claim: TargetClaim, fact: ProjectFact) -> tuple[str, str]:
    claim_date = claim.attributes.date_value if claim.attributes else None
    fact_date = fact.attributes.date_value if fact.attributes else None
    subject = _subject_label(claim)
    date_detail = ""
    if claim_date and fact_date:
        date_detail = f" (target {claim_date}, reference {fact_date})"
    return (
        f"Target date for {subject} conflicts with reference{date_detail}",
        (
            f"Target uses {_truncate(claim.text, 100)}, but reference says "
            f"{_truncate(fact.text or fact.evidence.quote, 120)}"
        ),
    )


def responsibility_conflict_copy(claim: TargetClaim, fact: ProjectFact) -> tuple[str, str]:
    subject = _subject_label(claim)
    return (
        f"Responsibility for {subject} conflicts with reference source",
        (
            f"Target assigns {_truncate(claim.text, 100)}, but reference says "
            f"{_truncate(fact.text or fact.evidence.quote, 120)}"
        ),
    )


def change_control_copy(claim: TargetClaim, fact: ProjectFact) -> tuple[str, str]:
    return (
        "Change-control language conflicts with signed process",
        (
            f"Target allows informal scope changes ({_truncate(claim.text, 100)}), "
            f"but reference requires signed change control: "
            f"{_truncate(fact.evidence.quote, 120)}"
        ),
    )


def authority_mismatch_copy(claim: TargetClaim, facts: list[ProjectFact]) -> tuple[str, str]:
    subject = _subject_label(claim)
    ref_snippet = _truncate(facts[0].evidence.quote, 120) if facts else ""
    return (
        f"Unapproved request for {subject} presented as included scope",
        (
            f"Target treats {_truncate(claim.text, 100)} as approved scope, but "
            f"reference only shows an informal request or proposed change: {ref_snippet}"
        ),
    )


def unsupported_claim_copy(claim: TargetClaim) -> tuple[str, str]:
    subject = _subject_label(claim)
    return (
        f"Unsupported target claim: {subject}",
        (
            f"This claim is not supported by uploaded reference materials and should be "
            f"verified: {_truncate(claim.text, 140)}"
        ),
    )


def vague_requirement_copy(claim: TargetClaim) -> tuple[str, str]:
    return (
        "Vague requirement",
        (
            f"This requirement uses vague language that may be difficult to test or verify: "
            f"{_truncate(claim.text, 140)}"
        ),
    )


def missing_ac_copy(claim: TargetClaim) -> tuple[str, str]:
    req_id = claim.attributes.requirement_id if claim.attributes else None
    label = req_id or _subject_label(claim)
    return (
        f"Missing acceptance criteria for {label}",
        (
            f"Requirement {_truncate(claim.text, 120)} has no matching acceptance criteria."
        ),
    )


def missing_date_copy(claim: TargetClaim) -> tuple[str, str]:
    return (
        "Missing date value",
        (
            f"This date-related claim lacks a concrete date value: "
            f"{_truncate(claim.text, 140)}"
        ),
    )


def uat_missing_result_copy(claim: TargetClaim) -> tuple[str, str]:
    test_id = claim.attributes.test_id if claim.attributes else None
    label = test_id or _subject_label(claim)
    return (
        f"UAT test {label} missing expected result",
        (
            f"This UAT test does not include a clear expected result: "
            f"{_truncate(claim.text, 140)}"
        ),
    )


def uat_coverage_gap_copy(subject: str, requirement_id: str | None = None) -> tuple[str, str]:
    label = requirement_id or subject.replace("_", " ")
    return (
        f"UAT coverage gap for {label}",
        f"Reference requirement '{label}' has no matching UAT test in the target plan.",
    )


def unresolved_conflict_copy(claim: TargetClaim, facts: list[ProjectFact]) -> tuple[str, str]:
    subject = _subject_label(claim)
    return (
        f"Unresolved reference conflict on {subject}",
        (
            f"Reference materials disagree on {subject} and the target relies on one side: "
            f"{_truncate(claim.text, 100)}"
        ),
    )
