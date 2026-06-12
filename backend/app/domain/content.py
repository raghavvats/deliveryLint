"""Missing expected content computation."""

from backend.app.schemas.enums import FactCategory


def compute_missing_expected_content(
    expected_content: list[FactCategory],
    observed_content: list[FactCategory],
) -> list[FactCategory]:
    observed = set(observed_content)
    return [category for category in expected_content if category not in observed]
