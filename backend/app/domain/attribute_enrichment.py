"""Post-extraction enrichment for structured claim/fact attributes."""

from __future__ import annotations

import re
from datetime import date

from backend.app.schemas.project_fact import ProjectFact, ProjectFactAttributes
from backend.app.schemas.target_document import TargetClaim

ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

# "week of March 10", "early May", "before launch" lack ISO dates — left to rubric rules.
OWNER_FROM_TEXT_RE = re.compile(
    r"\b(?:owner|assigned to|responsible party)[:\s]+([A-Za-z][A-Za-z0-9\s.-]{1,40})",
    re.IGNORECASE,
)


def extract_iso_date(text: str) -> date | None:
    match = ISO_DATE_RE.search(text)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def extract_owner_from_text(text: str) -> str | None:
    match = OWNER_FROM_TEXT_RE.search(text)
    if match:
        return match.group(1).strip()
    return None


def enrich_fact_attributes(fact: ProjectFact) -> ProjectFact:
    attrs = fact.attributes.model_copy() if fact.attributes else ProjectFactAttributes()
    changed = False

    if attrs.date_value is None:
        parsed = extract_iso_date(fact.text) or extract_iso_date(fact.evidence.quote)
        if parsed is not None:
            attrs.date_value = parsed
            changed = True

    if not attrs.owner:
        owner = extract_owner_from_text(fact.text) or extract_owner_from_text(fact.evidence.quote)
        if owner:
            attrs.owner = owner
            changed = True

    if not changed:
        return fact
    return fact.model_copy(update={"attributes": attrs})


def enrich_claim_attributes(claim: TargetClaim) -> TargetClaim:
    attrs = claim.attributes.model_copy() if claim.attributes else ProjectFactAttributes()
    changed = False

    if attrs.date_value is None:
        quote = claim.location.quote if claim.location else ""
        parsed = extract_iso_date(claim.text) or extract_iso_date(quote)
        if parsed is not None:
            attrs.date_value = parsed
            changed = True

    if not attrs.owner:
        quote = claim.location.quote if claim.location else ""
        owner = extract_owner_from_text(claim.text) or extract_owner_from_text(quote)
        if owner:
            attrs.owner = owner
            changed = True

    if not changed:
        return claim
    return claim.model_copy(update={"attributes": attrs})
