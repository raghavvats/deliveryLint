"""Completeness lint rules."""

from uuid import uuid4

from backend.app.schemas.enums import LintFindingType
from backend.app.schemas.lint import LintContext, LintFinding
from backend.app.services.lint_engine.severity import severity_for_missing_content


def run_completeness_rules(context: LintContext) -> list[LintFinding]:
    findings: list[LintFinding] = []
    profile = context.target_profile
    target_document_id = profile.document_id

    for category in profile.missing_expected_content:
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
                recommendation=(
                    f"Add content covering {category.value} that is normally expected "
                    f"for a {profile.doc_type.value}."
                ),
                rule_id=f"completeness.missing_expected_content.{category.value}",
            )
        )

    return findings
