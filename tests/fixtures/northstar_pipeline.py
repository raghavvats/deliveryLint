"""Deterministic structured fixtures for the Northstar Components synthetic case.

The production pipeline relies on an LLM to parse the target document and extract
reference facts, which is non-deterministic. For regression testing we instead
feed pre-extracted, structured LLM responses through the *real* downstream
pipeline (target validation -> fact validation -> clustering -> matching ->
classification -> review-priority).

Key design choice: the ``normalized_subject`` values on target claims are
deliberately NOT identical to those on the matching reference facts (e.g.
``netsuite_billing_sync`` vs ``netsuite_billing_integration``). This proves the
engine matches by meaning rather than exact string equality, which is the core
bug being fixed.

The raw synthetic ``.md`` documents live alongside this module in
``tests/fixtures/northstar/`` for provenance.
"""

from datetime import date
from pathlib import Path

from backend.app.schemas.enums import (
    DateType,
    DocType,
    FactCategory,
    FactPolarity,
    FactStatus,
    FactType,
    ReliabilityFlag,
    SourceOrigin,
    SourceStatus,
)
from backend.app.schemas.fact_parser import ProjectFactLLMOutput, ProjectFactLLMResponse
from backend.app.schemas.project_fact import EvidenceSpan, ProjectFactAttributes
from backend.app.schemas.source_profile import SourceProfileInference
from backend.app.schemas.target_document import TargetLocation
from backend.app.schemas.target_parser import (
    TargetClaimLLMOutput,
    TargetDocumentLLMResponse,
    TargetSectionLLMOutput,
)
from backend.app.schemas.upload import (
    CustomLintRequest,
    ReferenceProfileHints,
    ReferenceUpload,
    UploadedDocument,
)
from backend.app.services.llm_client import MockLLMClient

DOCS_DIR = Path(__file__).parent / "northstar"

TARGET_DOC_ID = "northstar_target_draft_sow"
SIGNED_SOW_DOC_ID = "northstar_signed_sow"
REQUIREMENTS_DOC_ID = "northstar_requirements_doc"
UAT_PLAN_DOC_ID = "northstar_uat_plan"
CLIENT_EMAIL_DOC_ID = "northstar_client_email"
MEETING_NOTES_DOC_ID = "northstar_meeting_notes"


def _read(filename: str) -> str:
    return (DOCS_DIR / filename).read_text(encoding="utf-8")


def _loc(quote: str) -> TargetLocation:
    return TargetLocation(quote=quote, section_title=None)


def _loc_section(quote: str, section_title: str) -> TargetLocation:
    return TargetLocation(quote=quote, section_title=section_title)


# ---------------------------------------------------------------------------
# Source profile inferences (doc-type / status / observed content per reference)
# ---------------------------------------------------------------------------

MOCK_SOURCE_INFERENCES: dict[str, SourceProfileInference] = {
    SIGNED_SOW_DOC_ID: SourceProfileInference(
        inferred_doc_type=DocType.SIGNED_SOW,
        doc_type_confidence=0.98,
        inferred_origin=SourceOrigin.JOINT,
        origin_confidence=0.9,
        inferred_status=SourceStatus.SIGNED,
        status_confidence=0.96,
        inferred_recency_date=date(2026, 5, 15),
        recency_date_confidence=0.9,
        observed_content=[
            FactCategory.SCOPE,
            FactCategory.OUT_OF_SCOPE,
            FactCategory.DELIVERABLES,
            FactCategory.DATES,
            FactCategory.RESPONSIBILITIES,
            FactCategory.ASSUMPTIONS,
            FactCategory.DEPENDENCIES,
            FactCategory.SYSTEMS,
            FactCategory.ACCEPTANCE_CRITERIA,
            FactCategory.CHANGE_REQUESTS,
        ],
        reliability_flags=[],
        summary="Signed, controlling SOW defining official CPQ scope, exclusions, and timeline.",
    ),
    REQUIREMENTS_DOC_ID: SourceProfileInference(
        inferred_doc_type=DocType.REQUIREMENTS_DOC,
        doc_type_confidence=0.95,
        inferred_origin=SourceOrigin.JOINT,
        origin_confidence=0.88,
        inferred_status=SourceStatus.APPROVED,
        status_confidence=0.93,
        inferred_recency_date=date(2026, 6, 5),
        recency_date_confidence=0.9,
        observed_content=[
            FactCategory.REQUIREMENTS,
            FactCategory.ACCEPTANCE_CRITERIA,
            FactCategory.SYSTEMS,
        ],
        reliability_flags=[],
        summary="Approved requirements document with measurable acceptance criteria.",
    ),
    UAT_PLAN_DOC_ID: SourceProfileInference(
        inferred_doc_type=DocType.UAT_PLAN,
        doc_type_confidence=0.95,
        inferred_origin=SourceOrigin.JOINT,
        origin_confidence=0.88,
        inferred_status=SourceStatus.APPROVED,
        status_confidence=0.92,
        inferred_recency_date=date(2026, 7, 8),
        recency_date_confidence=0.9,
        observed_content=[
            FactCategory.UAT_TESTS,
            FactCategory.ACCEPTANCE_CRITERIA,
            FactCategory.RESPONSIBILITIES,
            FactCategory.DATES,
        ],
        reliability_flags=[],
        summary="Approved UAT plan; Northstar owns execution with Auctor support.",
    ),
    CLIENT_EMAIL_DOC_ID: SourceProfileInference(
        inferred_doc_type=DocType.CLIENT_EMAIL,
        doc_type_confidence=0.92,
        inferred_origin=SourceOrigin.CLIENT,
        origin_confidence=0.9,
        inferred_status=SourceStatus.INFORMAL,
        status_confidence=0.9,
        inferred_recency_date=date(2026, 6, 12),
        recency_date_confidence=0.85,
        observed_content=[FactCategory.CLIENT_REQUESTS, FactCategory.SYSTEMS],
        reliability_flags=[ReliabilityFlag.INFORMAL_SOURCE],
        summary="Informal client email requesting evaluation of NetSuite billing sync.",
    ),
    MEETING_NOTES_DOC_ID: SourceProfileInference(
        inferred_doc_type=DocType.MEETING_TRANSCRIPT,
        doc_type_confidence=0.9,
        inferred_origin=SourceOrigin.JOINT,
        origin_confidence=0.85,
        inferred_status=SourceStatus.TRANSCRIPT,
        status_confidence=0.85,
        inferred_recency_date=date(2026, 6, 11),
        recency_date_confidence=0.85,
        observed_content=[
            FactCategory.DECISIONS,
            FactCategory.DATES,
            FactCategory.CLIENT_REQUESTS,
            FactCategory.SYSTEMS,
        ],
        reliability_flags=[],
        summary="Sprint-planning notes confirming Aug 1 go-live and NetSuite out of scope.",
    ),
}


# ---------------------------------------------------------------------------
# Reference facts
# ---------------------------------------------------------------------------

MOCK_FACT_RESPONSES: dict[str, ProjectFactLLMResponse] = {
    SIGNED_SOW_DOC_ID: ProjectFactLLMResponse(
        facts=[
            # --- Explicit exclusions ---
            ProjectFactLLMOutput(
                fact_type=FactType.OUT_OF_SCOPE_ITEM,
                text="NetSuite billing integration, billing sync, invoice/order creation, and ERP posting are out of scope.",
                subject="NetSuite billing integration",
                normalized_subject="netsuite_billing_integration",
                # Realistic extraction: "X is out of scope" is asserted positively,
                # so the polarity label is not reliably NEGATIVE.
                polarity=FactPolarity.NEUTRAL,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="NetSuite billing integration, billing sync, invoice creation, order creation, or ERP posting."
                ),
                extraction_confidence=0.97,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.OUT_OF_SCOPE_ITEM,
                text="Customer portal, distributor portal, and online quote acceptance are out of scope.",
                subject="Customer portal online quote acceptance",
                normalized_subject="customer_portal_online_quote_acceptance",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="Customer portal, distributor portal, online quote acceptance, e-signature, or self-service ordering functionality."
                ),
                extraction_confidence=0.97,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.OUT_OF_SCOPE_ITEM,
                text="No NetSuite, ERP, billing, tax, portal, or middleware access is required for this release.",
                subject="NetSuite access",
                normalized_subject="netsuite_access",
                polarity=FactPolarity.NEUTRAL,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="No NetSuite, ERP, billing, tax, portal, or middleware access is required for this first release."
                ),
                extraction_confidence=0.95,
            ),
            # --- Authoritative date ---
            ProjectFactLLMOutput(
                fact_type=FactType.DATE,
                text="Production go-live is August 1, 2026.",
                subject="Production go-live",
                normalized_subject="production_go_live_date",
                polarity=FactPolarity.NEUTRAL,
                fact_status=FactStatus.SIGNED,
                attributes=ProjectFactAttributes(
                    date_type=DateType.GO_LIVE, date_value=date(2026, 8, 1)
                ),
                evidence=EvidenceSpan(quote="Production go-live: August 1, 2026"),
                extraction_confidence=0.97,
            ),
            # --- Responsibility: Northstar owns UAT execution ---
            ProjectFactLLMOutput(
                fact_type=FactType.CLIENT_RESPONSIBILITY,
                text="Northstar owns and executes UAT test scripts with support from Auctor Systems.",
                subject="UAT execution",
                normalized_subject="uat_execution",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                # Realistic extraction: owner attribute not populated; the party is
                # only evident from the responsibility type and sentence text.
                evidence=EvidenceSpan(
                    quote="Own and execute UAT test scripts with support from Auctor Systems."
                ),
                extraction_confidence=0.95,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.CLIENT_RESPONSIBILITY,
                text="Northstar will identify UAT participants.",
                subject="Identify UAT participants",
                normalized_subject="identify_uat_participants",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                attributes=ProjectFactAttributes(owner="Northstar"),
                evidence=EvidenceSpan(quote="Northstar will identify UAT participants by June 19."),
                extraction_confidence=0.9,
            ),
            # --- Change control ---
            ProjectFactLLMOutput(
                fact_type=FactType.CHANGE_REQUEST,
                text="Changes require a written change request signed by both sponsors; informal notes are not approved scope.",
                subject="Change control approval",
                normalized_subject="change_control_signed_approval",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="A change request is approved only when signed by the Northstar executive sponsor and the Auctor engagement manager."
                ),
                extraction_confidence=0.9,
            ),
            # --- Northstar-owned access provisioning. Shares only the GENERIC token
            #     "access" with the Auctor "administrator access" responsibility, so a
            #     correct engine must NOT treat them as the same responsibility even
            #     though owners differ.
            ProjectFactLLMOutput(
                fact_type=FactType.CLIENT_RESPONSIBILITY,
                text="Northstar will provision system and environment access for the project.",
                subject="System and environment access provisioning",
                normalized_subject="system_access_provisioning",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                attributes=ProjectFactAttributes(owner="Northstar"),
                evidence=EvidenceSpan(
                    quote="Northstar will provision system and environment access for the project."
                ),
                extraction_confidence=0.9,
            ),
            # --- Legitimate in-scope items (so the target's matching claims are SUPPORTED) ---
            ProjectFactLLMOutput(
                fact_type=FactType.SCOPE_ITEM,
                text="Product catalog and product hierarchy setup for ~850 active SKUs.",
                subject="Product catalog and hierarchy setup",
                normalized_subject="product_catalog_hierarchy_setup",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="Product catalog and product hierarchy setup for approximately 850 active SKUs."
                ),
                extraction_confidence=0.95,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.SCOPE_ITEM,
                text="Price book configuration for list, customer-specific, and volume discount pricing.",
                subject="Price book configuration",
                normalized_subject="price_book_setup",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="Price book configuration for standard list pricing, customer-specific pricing, and approved volume discount tiers."
                ),
                extraction_confidence=0.95,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.SCOPE_ITEM,
                text="Quote document generation using one approved customer-facing template.",
                subject="Quote document generation template",
                normalized_subject="quote_document_generation_template",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="Quote document generation using one approved Northstar customer-facing quote template."
                ),
                extraction_confidence=0.95,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.SCOPE_ITEM,
                text="Discount approval workflows for thresholds and margin exceptions.",
                subject="Discount approval workflows",
                normalized_subject="discount_approval_workflows",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.SIGNED,
                evidence=EvidenceSpan(
                    quote="Discount approval workflows for quote-level discount thresholds and margin exception review."
                ),
                extraction_confidence=0.95,
            ),
        ]
    ),
    REQUIREMENTS_DOC_ID: ProjectFactLLMResponse(
        facts=[
            ProjectFactLLMOutput(
                fact_type=FactType.REQUIREMENT,
                text="Configure standard list, customer-specific, and volume discount pricing.",
                subject="Pricing configuration requirement",
                normalized_subject="price_book_setup",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.APPROVED,
                attributes=ProjectFactAttributes(requirement_id="REQ-004", owner="Auctor"),
                evidence=EvidenceSpan(
                    quote="Configure standard list pricing, customer-specific pricing, and approved volume discount tiers."
                ),
                extraction_confidence=0.92,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.REQUIREMENT,
                text="Generate one approved customer-facing quote PDF template.",
                subject="Quote PDF template requirement",
                normalized_subject="quote_document_generation_template",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.APPROVED,
                attributes=ProjectFactAttributes(requirement_id="REQ-006", owner="Auctor"),
                evidence=EvidenceSpan(quote="Generate one approved customer-facing quote PDF template."),
                extraction_confidence=0.92,
            ),
        ]
    ),
    UAT_PLAN_DOC_ID: ProjectFactLLMResponse(
        facts=[
            ProjectFactLLMOutput(
                fact_type=FactType.CLIENT_RESPONSIBILITY,
                text="UAT is executed by Northstar business users with Auctor support.",
                subject="UAT execution responsibility",
                normalized_subject="uat_test_execution",
                polarity=FactPolarity.POSITIVE,
                fact_status=FactStatus.APPROVED,
                attributes=ProjectFactAttributes(owner="Northstar"),
                evidence=EvidenceSpan(
                    quote="UAT will be executed by Northstar business users with support from Auctor Systems."
                ),
                extraction_confidence=0.92,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.DATE,
                text="Production go-live is August 1, 2026.",
                subject="Go-live date",
                normalized_subject="go_live_date",
                polarity=FactPolarity.NEUTRAL,
                fact_status=FactStatus.APPROVED,
                attributes=ProjectFactAttributes(
                    date_type=DateType.GO_LIVE, date_value=date(2026, 8, 1)
                ),
                evidence=EvidenceSpan(quote="before the August 1, 2026 production go-live"),
                extraction_confidence=0.9,
            ),
        ]
    ),
    CLIENT_EMAIL_DOC_ID: ProjectFactLLMResponse(
        facts=[
            ProjectFactLLMOutput(
                fact_type=FactType.CLIENT_REQUEST,
                text="Client asked Auctor to evaluate adding NetSuite billing sync; explicitly a request, not an approval.",
                subject="NetSuite billing sync request",
                normalized_subject="netsuite_billing_sync",
                polarity=FactPolarity.NEUTRAL,
                fact_status=FactStatus.REQUESTED,
                evidence=EvidenceSpan(
                    quote="please treat this as a request for evaluation rather than a formal approval."
                ),
                extraction_confidence=0.9,
            ),
        ]
    ),
    MEETING_NOTES_DOC_ID: ProjectFactLLMResponse(
        facts=[
            ProjectFactLLMOutput(
                fact_type=FactType.DECISION,
                text="August 1, 2026 remains the official production go-live date.",
                subject="Official go-live decision",
                normalized_subject="go_live_date",
                polarity=FactPolarity.NEUTRAL,
                fact_status=FactStatus.CONFIRMED,
                attributes=ProjectFactAttributes(
                    date_type=DateType.GO_LIVE, date_value=date(2026, 8, 1)
                ),
                evidence=EvidenceSpan(quote="August 1, 2026 remains the official production go-live date."),
                extraction_confidence=0.9,
            ),
            ProjectFactLLMOutput(
                fact_type=FactType.DECISION,
                text="NetSuite billing sync is not approved scope and requires signed change control.",
                subject="NetSuite billing sync not approved",
                normalized_subject="netsuite_billing_sync",
                polarity=FactPolarity.NEGATIVE,
                fact_status=FactStatus.CONFIRMED,
                evidence=EvidenceSpan(
                    quote="NetSuite billing sync is not approved scope and will not be added to Release 1 without signed change control."
                ),
                extraction_confidence=0.9,
            ),
        ]
    ),
}


# ---------------------------------------------------------------------------
# Target claims (subjects intentionally differ from reference fact subjects)
# ---------------------------------------------------------------------------

MOCK_TARGET_RESPONSES: dict[str, TargetDocumentLLMResponse] = {
    TARGET_DOC_ID: TargetDocumentLLMResponse(
        observed_content=[
            FactCategory.SCOPE,
            FactCategory.DELIVERABLES,
            FactCategory.DATES,
            FactCategory.RESPONSIBILITIES,
            FactCategory.ASSUMPTIONS,
            FactCategory.DEPENDENCIES,
            FactCategory.SYSTEMS,
            FactCategory.ACCEPTANCE_CRITERIA,
            FactCategory.CHANGE_REQUESTS,
            FactCategory.OUT_OF_SCOPE,
        ],
        sections=[
            TargetSectionLLMOutput(
                title="In-Scope Services",
                normalized_title="scope",
                text="Scope including NetSuite billing sync and customer portal acceptance.",
                content_categories=[FactCategory.SCOPE, FactCategory.SYSTEMS],
                location=TargetLocation(section_title="In-Scope Services"),
            ),
        ],
        claims=[
            # === Seeded issue 1: NetSuite billing sync presented as in scope ===
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="NetSuite billing sync for approved quotes, transmitting quote data from Salesforce CPQ to NetSuite.",
                subject="NetSuite billing sync",
                normalized_subject="netsuite_billing_sync",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("NetSuite billing sync for approved quotes"),
                checkable=True,
                extraction_confidence=0.95,
            ),
            # === Seeded issue 9/13: Customer portal quote acceptance in scope ===
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="Customer portal quote acceptance so distributors can review and accept quotes online.",
                subject="Customer portal quote acceptance",
                normalized_subject="customer_portal_quote_acceptance",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("Customer portal quote acceptance so distributors can review and accept quotes online"),
                checkable=True,
                extraction_confidence=0.95,
            ),
            # === Seeded issue 10: NetSuite billing integration design deliverable ===
            TargetClaimLLMOutput(
                claim_type=FactType.DELIVERABLE,
                text="NetSuite billing integration design: design and field mapping for NetSuite billing sync.",
                subject="NetSuite billing integration design",
                normalized_subject="netsuite_billing_integration_design",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("NetSuite billing integration design"),
                checkable=True,
                extraction_confidence=0.9,
            ),
            # === Seeded issue 9: Customer portal prototype deliverable ===
            TargetClaimLLMOutput(
                claim_type=FactType.DELIVERABLE,
                text="Customer portal quote acceptance prototype allowing distributors to accept quotes online.",
                subject="Customer portal quote acceptance prototype",
                normalized_subject="customer_portal_acceptance_prototype",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("Customer portal quote acceptance prototype"),
                checkable=True,
                extraction_confidence=0.9,
            ),
            # === Seeded issue 3: go-live date Aug 15 vs Aug 1 ===
            TargetClaimLLMOutput(
                claim_type=FactType.DATE,
                text="Production go-live targeted for August 15, 2026.",
                subject="Production go-live",
                normalized_subject="production_go_live",
                polarity=FactPolarity.NEUTRAL,
                claim_status=FactStatus.PROPOSED,
                attributes=ProjectFactAttributes(
                    date_type=DateType.GO_LIVE, date_value=date(2026, 8, 15)
                ),
                location=_loc("production go-live targeted for August 15, 2026"),
                checkable=True,
                extraction_confidence=0.95,
            ),
            # === Seeded issue 7: Auctor executes UAT ===
            TargetClaimLLMOutput(
                claim_type=FactType.TEAM_RESPONSIBILITY,
                text="Auctor Systems will define and execute all UAT test scripts on behalf of Northstar business users.",
                subject="UAT test script execution",
                normalized_subject="uat_test_script_execution",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("Define and execute all UAT test scripts on behalf of Northstar business users."),
                checkable=True,
                extraction_confidence=0.92,
            ),
            # === Seeded issue 11: NetSuite sandbox/API credentials dependency ===
            TargetClaimLLMOutput(
                claim_type=FactType.DEPENDENCY,
                text="Northstar will provide NetSuite sandbox access and API credentials by June 19, 2026.",
                subject="NetSuite sandbox access and API credentials",
                normalized_subject="netsuite_sandbox_api_credentials",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                attributes=ProjectFactAttributes(owner="Northstar"),
                location=_loc("Northstar will provide NetSuite sandbox access and API credentials by June 19, 2026."),
                checkable=True,
                extraction_confidence=0.9,
            ),
            # === Seeded issue: weak change control vs signed change-control rule ===
            TargetClaimLLMOutput(
                claim_type=FactType.CHANGE_REQUEST,
                text="Items that can be accommodated may be incorporated into the active sprint backlog with agreement from the project team.",
                subject="Change control via sprint backlog",
                normalized_subject="change_control_sprint_backlog",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("incorporated into the active sprint backlog with agreement from the project team"),
                checkable=True,
                extraction_confidence=0.9,
            ),
            # === Seeded issue 5: vague language ===
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="The CPQ solution should be fast, user-friendly, and seamless for Northstar's sales users.",
                subject="CPQ user experience",
                normalized_subject="cpq_user_experience_quality",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("The CPQ solution should be fast, user-friendly, and seamless"),
                checkable=True,
                extraction_confidence=0.85,
            ),
            # === Legitimate in-scope items: must NOT be flagged unsupported ===
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="Product catalog setup for approximately 850 active SKUs and up to 40 product bundles.",
                subject="Product catalog setup",
                normalized_subject="product_catalog_setup_850_skus",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("Product catalog setup for approximately 850 active SKUs and up to 40 product bundles."),
                checkable=True,
                extraction_confidence=0.92,
            ),
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="Price book configuration for list pricing, customer-specific pricing, and volume discounting.",
                subject="Price book configuration",
                normalized_subject="price_book_configuration",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("Price book configuration for list pricing, customer-specific pricing, and volume discounting."),
                checkable=True,
                extraction_confidence=0.92,
            ),
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="Quote PDFs are generated using the approved Northstar quote template.",
                subject="Quote PDF generation",
                normalized_subject="quote_pdf_template",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("Quote PDFs are generated using the approved Northstar quote template."),
                checkable=True,
                extraction_confidence=0.92,
            ),
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="Discount approval workflow for non-standard discounts and margin exceptions.",
                subject="Discount approval workflow",
                normalized_subject="discount_approval_workflow",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc("Discount approval workflow for non-standard discounts and margin exceptions."),
                checkable=True,
                extraction_confidence=0.92,
            ),
            TargetClaimLLMOutput(
                claim_type=FactType.CLIENT_RESPONSIBILITY,
                text="Northstar will identify UAT participants from sales operations, inside sales, finance, and sales leadership.",
                subject="UAT participant identification",
                normalized_subject="uat_participant_identification",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                attributes=ProjectFactAttributes(owner="Northstar"),
                location=_loc("Northstar will identify UAT participants from sales operations, inside sales, finance, and sales leadership."),
                checkable=True,
                extraction_confidence=0.9,
            ),
            # === False positive guard: Sales Cloud object integration must NOT
            #     match the NetSuite "integration" exclusion (generic token only). ===
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="Integration with Salesforce Sales Cloud objects including Account, Opportunity, Product, Price Book, Quote, Quote Line, and Contract.",
                subject="Salesforce Sales Cloud object integration",
                normalized_subject="salesforce_sales_cloud_object_integration",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc_section(
                    "Integration with Salesforce Sales Cloud objects including Account, Opportunity, Product, Price Book, Quote, Quote Line, and Contract.",
                    "In-Scope Services",
                ),
                checkable=True,
                extraction_confidence=0.92,
            ),
            # === False positive guard: an item under "Out-of-Scope Items" that the
            #     extractor mislabelled positive must keep out-of-scope polarity and
            #     not become a contradiction. ===
            TargetClaimLLMOutput(
                claim_type=FactType.SCOPE_ITEM,
                text="Major redesign of Sales Cloud opportunity management.",
                subject="Sales Cloud opportunity management redesign",
                normalized_subject="sales_cloud_opportunity_management_redesign",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc_section(
                    "Major redesign of Sales Cloud opportunity management.",
                    "Out-of-Scope Items",
                ),
                checkable=True,
                extraction_confidence=0.9,
            ),
            # === False positive guard: Auctor's admin-access responsibility must NOT
            #     conflict with an unrelated Northstar project-governance responsibility. ===
            TargetClaimLLMOutput(
                claim_type=FactType.TEAM_RESPONSIBILITY,
                text="Auctor Systems will have access to a Northstar Salesforce system administrator for configuration review and deployment support.",
                subject="Salesforce administrator access",
                normalized_subject="salesforce_administrator_access",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                attributes=ProjectFactAttributes(owner="Auctor Systems"),
                location=_loc_section(
                    "Auctor Systems will have access to a Northstar Salesforce system administrator for configuration review and deployment support.",
                    "Assumptions and Dependencies",
                ),
                checkable=True,
                extraction_confidence=0.9,
            ),
            # === False positive guard: sentences naming an explicit owner must NOT
            #     produce a missing-owner finding even when no owner attribute is set. ===
            TargetClaimLLMOutput(
                claim_type=FactType.TEAM_RESPONSIBILITY,
                text="Auctor Systems will lead discovery validation, Salesforce CPQ configuration, training, and deployment support.",
                subject="Auctor delivery leadership",
                normalized_subject="auctor_delivery_leadership",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc_section(
                    "Auctor Systems will lead discovery validation, Salesforce CPQ configuration, training, and deployment support.",
                    "Overview",
                ),
                checkable=True,
                extraction_confidence=0.9,
            ),
            TargetClaimLLMOutput(
                claim_type=FactType.CLIENT_RESPONSIBILITY,
                text="Northstar will provide project sponsorship and business owner participation.",
                subject="Northstar sponsorship",
                normalized_subject="northstar_sponsorship_participation",
                polarity=FactPolarity.POSITIVE,
                claim_status=FactStatus.PROPOSED,
                location=_loc_section(
                    "Northstar will provide project sponsorship and business owner participation.",
                    "Roles and Responsibilities",
                ),
                checkable=True,
                extraction_confidence=0.9,
            ),
        ],
    ),
}


def build_northstar_mock_client() -> MockLLMClient:
    return MockLLMClient(
        source_inferences=MOCK_SOURCE_INFERENCES,
        fact_responses=MOCK_FACT_RESPONSES,
        target_responses=MOCK_TARGET_RESPONSES,
    )


def build_northstar_request(project_id: str = "northstar_test") -> CustomLintRequest:
    return CustomLintRequest(
        project_id=project_id,
        target=UploadedDocument(
            document_id=TARGET_DOC_ID,
            filename="target_draft_sow.md",
            text=_read("target_draft_sow.md"),
        ),
        target_doc_type=DocType.DRAFT_SOW,
        references=[
            ReferenceUpload(
                document_id=SIGNED_SOW_DOC_ID,
                filename="reference_signed_sow.md",
                text=_read("reference_signed_sow.md"),
                profile_hints=ReferenceProfileHints(
                    user_provided_doc_type=DocType.SIGNED_SOW,
                    user_provided_origin=SourceOrigin.JOINT,
                    user_provided_status=SourceStatus.SIGNED,
                ),
            ),
            ReferenceUpload(
                document_id=REQUIREMENTS_DOC_ID,
                filename="reference_requirements_doc.md",
                text=_read("reference_requirements_doc.md"),
                profile_hints=ReferenceProfileHints(
                    user_provided_doc_type=DocType.REQUIREMENTS_DOC,
                    user_provided_origin=SourceOrigin.JOINT,
                    user_provided_status=SourceStatus.APPROVED,
                ),
            ),
            ReferenceUpload(
                document_id=UAT_PLAN_DOC_ID,
                filename="reference_uat_plan.md",
                text=_read("reference_uat_plan.md"),
                profile_hints=ReferenceProfileHints(
                    user_provided_doc_type=DocType.UAT_PLAN,
                    user_provided_origin=SourceOrigin.JOINT,
                    user_provided_status=SourceStatus.APPROVED,
                ),
            ),
            ReferenceUpload(
                document_id=CLIENT_EMAIL_DOC_ID,
                filename="reference_client_email.md",
                text=_read("reference_client_email.md"),
                profile_hints=ReferenceProfileHints(
                    user_provided_doc_type=DocType.CLIENT_EMAIL,
                    user_provided_origin=SourceOrigin.CLIENT,
                    user_provided_status=SourceStatus.INFORMAL,
                ),
            ),
            ReferenceUpload(
                document_id=MEETING_NOTES_DOC_ID,
                filename="reference_meeting_notes.md",
                text=_read("reference_meeting_notes.md"),
                profile_hints=ReferenceProfileHints(
                    user_provided_doc_type=DocType.MEETING_TRANSCRIPT,
                    user_provided_origin=SourceOrigin.JOINT,
                    user_provided_status=SourceStatus.TRANSCRIPT,
                ),
            ),
        ],
    )
