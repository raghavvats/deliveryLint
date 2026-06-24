"""Completeness lint rules."""

from uuid import uuid4

from backend.app.schemas.enums import DocType, FactCategory, LintFindingType
from backend.app.schemas.lint import LintContext, LintFinding
from backend.app.services.lint_engine.severity import severity_for_missing_content

CHANGE_ORDER_FEE_MARKERS = (
    "fee impact",
    "cost impact",
    "pricing impact",
    "additional fee",
    "fee adjustment",
    "cost adjustment",
    "total fee",
    "change fee",
)


def run_completeness_rules(context: LintContext) -> list[LintFinding]:
    findings: list[LintFinding] = []
    profile = context.target_profile
    target_document_id = profile.document_id
    target_text = " ".join(claim.text for claim in context.target_claims).lower()

    for category in profile.missing_expected_content:
        if (
            profile.doc_type == DocType.CHANGE_ORDER
            and category == FactCategory.CHANGE_REQUESTS
            and any(marker in target_text for marker in CHANGE_ORDER_FEE_MARKERS)
        ):
            continue
        severity = severity_for_missing_content(profile.doc_type, category)
        findings.append(
            LintFinding(
                id=f"finding_{uuid4().hex}",
                project_id=context.project_id,
                target_document_id=target_document_id,
                finding_type=LintFindingType.MISSING_EXPECTED_CONTENT,
                severity=severity,
                confidence=0.85,
                title=f"Missing expected {category.value} content",
                message=(
                    f"This {profile.doc_type.value} does not appear to include "
                    f"{category.value} content. That may reduce clarity or increase "
                    "delivery risk."
                ),
                rule_id=f"completeness.missing_expected_content.{category.value}",
            )
        )

    if profile.doc_type == DocType.CHANGE_ORDER:
        if not any(marker in target_text for marker in CHANGE_ORDER_FEE_MARKERS):
            if FactCategory.CHANGE_REQUESTS not in profile.missing_expected_content:
                findings.append(
                    LintFinding(
                        id=f"finding_{uuid4().hex}",
                        project_id=context.project_id,
                        target_document_id=target_document_id,
                        finding_type=LintFindingType.MISSING_EXPECTED_CONTENT,
                        severity=severity_for_missing_content(
                            profile.doc_type, FactCategory.CHANGE_REQUESTS
                        ),
                        confidence=0.8,
                        title="Missing expected fee impact content",
                        message=(
                            "This change order does not appear to include fee or cost "
                            "impact details required by signed change-control terms."
                        ),
                        rule_id="completeness.missing_fee_impact",
                    )
                )

    return findings
