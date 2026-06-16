"""Unit tests for out-of-scope section polarity preservation."""

import pytest

from backend.app.schemas.enums import FactPolarity, FactType
from backend.app.services.target_parser import _apply_section_polarity

_ALLOWED = [FactType.SCOPE_ITEM, FactType.OUT_OF_SCOPE_ITEM, FactType.DELIVERABLE]


def test_scope_item_under_out_of_scope_becomes_exclusion() -> None:
    claim_type, polarity = _apply_section_polarity(
        claim_type=FactType.SCOPE_ITEM,
        polarity=FactPolarity.POSITIVE,
        section_title="Out-of-Scope Items",
        allowed_claim_types=_ALLOWED,
    )
    assert claim_type == FactType.OUT_OF_SCOPE_ITEM
    assert polarity == FactPolarity.NEGATIVE


def test_deliverable_under_exclusions_flips_to_negative() -> None:
    claim_type, polarity = _apply_section_polarity(
        claim_type=FactType.DELIVERABLE,
        polarity=FactPolarity.POSITIVE,
        section_title="Exclusions",
        allowed_claim_types=_ALLOWED,
    )
    # Type is not reclassified (only SCOPE_ITEM is), but polarity is preserved.
    assert claim_type == FactType.DELIVERABLE
    assert polarity == FactPolarity.NEGATIVE


def test_in_scope_section_is_unchanged() -> None:
    claim_type, polarity = _apply_section_polarity(
        claim_type=FactType.SCOPE_ITEM,
        polarity=FactPolarity.POSITIVE,
        section_title="In-Scope Services",
        allowed_claim_types=_ALLOWED,
    )
    assert claim_type == FactType.SCOPE_ITEM
    assert polarity == FactPolarity.POSITIVE


def test_non_scope_claim_types_are_untouched() -> None:
    claim_type, polarity = _apply_section_polarity(
        claim_type=FactType.DATE,
        polarity=FactPolarity.NEUTRAL,
        section_title="Out of Scope",
        allowed_claim_types=_ALLOWED,
    )
    assert claim_type == FactType.DATE
    assert polarity == FactPolarity.NEUTRAL


@pytest.mark.parametrize("section", [None, "Deliverables", "Project Timeline"])
def test_no_override_without_exclusion_heading(section) -> None:
    claim_type, polarity = _apply_section_polarity(
        claim_type=FactType.SCOPE_ITEM,
        polarity=FactPolarity.POSITIVE,
        section_title=section,
        allowed_claim_types=_ALLOWED,
    )
    assert claim_type == FactType.SCOPE_ITEM
    assert polarity == FactPolarity.POSITIVE
