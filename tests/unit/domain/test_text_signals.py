"""Tests for deterministic text signal helpers."""

from backend.app.domain.text_signals import (
    claims_no_open_questions,
    extract_counts,
    extract_percentages,
    has_informal_change_control_language,
    has_relative_date_language,
    mentions_uat_execution,
)


def test_extract_percentages() -> None:
    assert extract_percentages("Discount approval workflow using a 10% approval threshold.") == {"10"}


def test_extract_counts() -> None:
    assert "12" in extract_counts("Admin training for up to 12 Nimbus users.")


def test_relative_date_language() -> None:
    assert has_relative_date_language("UAT will start in early May.")
    assert has_relative_date_language("Epic build workbook approval is targeted for the week of March 10.")


def test_informal_change_control() -> None:
    text = (
        "Small changes requested by Nimbus stakeholders may be handled during "
        "weekly check-ins without a formal signed change order."
    )
    assert has_informal_change_control_language(text)


def test_open_questions_none() -> None:
    assert claims_no_open_questions("None")


def test_uat_execution_marker() -> None:
    assert mentions_uat_execution("Auctor will own configuration, UAT execution, and credentials.")
