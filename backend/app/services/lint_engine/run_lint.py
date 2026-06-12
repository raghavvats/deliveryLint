"""Lint engine orchestration."""

from backend.app.schemas.lint import (
    LintContext,
    LintEngineWarning,
    LintEngineWarningCode,
    LintFinding,
    RunLintInput,
    RunLintOutput,
)
from backend.app.services.lint_engine.rules import RULE_MODULES
from backend.app.services.lint_engine.severity import SEVERITY_RANK


def build_lint_engine_warnings(context: LintContext) -> list[LintEngineWarning]:
    warnings: list[LintEngineWarning] = []

    if not context.source_profiles:
        warnings.append(
            LintEngineWarning(
                code=LintEngineWarningCode.NO_SOURCE_PROFILES,
                message="No source profiles were provided, so reference-grounding checks are limited.",
            )
        )

    if not context.project_facts:
        warnings.append(
            LintEngineWarning(
                code=LintEngineWarningCode.NO_REFERENCE_FACTS,
                message="No reference facts were provided, so grounding and contradiction checks are limited.",
            )
        )

    if not context.fact_clusters:
        warnings.append(
            LintEngineWarning(
                code=LintEngineWarningCode.NO_FACT_CLUSTERS,
                message="No fact clusters were provided, so unresolved-conflict checks are limited.",
            )
        )

    return warnings


def dedupe_and_sort_findings(findings: list[LintFinding]) -> list[LintFinding]:
    seen: set[tuple] = set()
    unique: list[LintFinding] = []

    for finding in findings:
        key = (
            finding.finding_type,
            finding.target_claim_id,
            finding.target_section_id,
            tuple(finding.related_fact_ids),
            finding.rule_id,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)

    return sorted(
        unique,
        key=lambda f: (
            -SEVERITY_RANK[f.severity],
            -f.confidence,
            f.target_claim_id or "",
        ),
    )


def run_lint(input: RunLintInput) -> RunLintOutput:
    context = LintContext(
        project_id=input.project_id,
        target_parse_result=input.target_parse_result,
        source_profiles=input.source_profiles,
        project_facts=input.project_facts,
        fact_clusters=input.fact_clusters,
    )

    warnings = build_lint_engine_warnings(context)
    findings: list[LintFinding] = []

    for rule_fn in RULE_MODULES:
        findings.extend(rule_fn(context))

    findings = dedupe_and_sort_findings(findings)

    return RunLintOutput(findings=findings, warnings=warnings)
