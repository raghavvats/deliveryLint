"""Unit tests for claim-classification helpers."""

from backend.app.services.lint_engine.rules.claim_classification import (
    _owner_from_text,
    _resolve_owner,
)


def test_owner_from_text_single_party() -> None:
    assert _owner_from_text("Auctor Systems will configure the solution.") == "vendor"
    assert _owner_from_text("Northstar will provide source data.") == "client"
    assert _owner_from_text("Nimbus will execute UAT.") == "client"
    assert _owner_from_text("The client will approve the design.") == "client"


def test_owner_from_text_ambiguous_returns_none() -> None:
    # Mentions both parties: ownership is ambiguous from text alone.
    text = "Auctor Systems will execute UAT on behalf of Northstar business users."
    assert _owner_from_text(text) is None


def test_owner_from_text_none_when_no_party() -> None:
    assert _owner_from_text("The system will generate quotes automatically.") is None


def test_resolve_owner_prefers_attribute() -> None:
    # Attribute wins even if the text is ambiguous.
    assert _resolve_owner("Auctor Systems", "Auctor and Northstar collaborate.") == "vendor"
    # Falls back to text when no attribute.
    assert _resolve_owner(None, "Northstar will provide access.") == "client"
