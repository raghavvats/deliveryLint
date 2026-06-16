"""Unit tests for normalized subject matching."""

import pytest

from backend.app.domain.normalization import is_out_of_scope_section
from backend.app.services.lint_engine.matching import (
    is_actionable_task,
    mentions_explicit_owner,
    subject_tokens,
    subjects_match,
    subjects_share_meaningful_term,
)


@pytest.mark.parametrize(
    "a, b",
    [
        ("netsuite_billing_sync", "netsuite_billing_integration"),
        ("customer_portal_quote_acceptance", "customer_portal"),
        ("production_go_live", "go_live_date"),
        ("product_catalog_setup_850_skus", "product_catalog_hierarchy_setup"),
        ("uat_test_script_execution", "uat_execution"),
        ("discount_approval_workflow", "discount_approval_workflows"),
    ],
)
def test_related_subjects_match(a: str, b: str) -> None:
    assert subjects_match(a, b)


@pytest.mark.parametrize(
    "a, b",
    [
        ("product_catalog_setup", "netsuite_billing_integration"),
        ("discount_approval_workflow", "customer_portal_quote_acceptance"),
        ("quote_pdf_template", "uat_execution"),
    ],
)
def test_unrelated_subjects_do_not_match(a: str, b: str) -> None:
    assert not subjects_match(a, b)


def test_stopwords_do_not_create_false_matches() -> None:
    # Two subjects that share only the generic stopword "salesforce" should not match.
    assert not subjects_match("salesforce_cpq_pricing", "salesforce_marketing_cloud")


def test_subject_tokens_drops_stopwords() -> None:
    assert subject_tokens("northstar_product_catalog") == {"product", "catalog"}


@pytest.mark.parametrize(
    "a, b",
    [
        # Shares the domain anchors netsuite/billing, not just "integration".
        ("netsuite_billing_sync", "netsuite_billing_integration"),
        ("customer_portal_quote_acceptance", "customer_portal_online_quote_acceptance"),
        ("netsuite_sandbox_api_credentials", "netsuite_access"),
    ],
)
def test_meaningful_overlap_true_for_shared_anchor(a: str, b: str) -> None:
    assert subjects_share_meaningful_term(a, b)


@pytest.mark.parametrize(
    "a, b",
    [
        # Shares only the generic word "integration".
        ("salesforce_sales_cloud_object_integration", "netsuite_billing_integration"),
        # Shares only the generic word "access".
        ("salesforce_administrator_access", "netsuite_access"),
        # Shares only the generic word "system".
        ("crm_system_setup", "manufacturing_execution_system"),
    ],
)
def test_meaningful_overlap_false_for_generic_only(a: str, b: str) -> None:
    assert not subjects_share_meaningful_term(a, b)


@pytest.mark.parametrize(
    "title",
    [
        "Out-of-Scope Items",
        "Out of Scope",
        "Exclusions",
        "Items Not in Scope",
    ],
)
def test_out_of_scope_section_detected(title: str) -> None:
    assert is_out_of_scope_section(title)


@pytest.mark.parametrize("title", ["In-Scope Services", "Deliverables", None])
def test_non_exclusion_sections_not_flagged(title) -> None:
    assert not is_out_of_scope_section(title)


@pytest.mark.parametrize(
    "text",
    [
        "Auctor Systems will lead discovery validation.",
        "Northstar will provide project sponsorship.",
        "The vendor will configure the system.",
        "The project team will review the design.",
    ],
)
def test_mentions_explicit_owner_true(text: str) -> None:
    assert mentions_explicit_owner(text)


def test_mentions_explicit_owner_false() -> None:
    assert not mentions_explicit_owner("Quotes are generated automatically.")


def test_is_actionable_task() -> None:
    assert is_actionable_task("Northstar will provide source data.")
    assert not is_actionable_task("Pricing data is materially complete.")
