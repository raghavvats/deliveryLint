"""Render harness run results as markdown for review in Cursor."""

from __future__ import annotations

from backend.app.test_harness.schemas import (
    ExpectedFindingResult,
    HarnessRunDetail,
    HarnessRunStatus,
    SuiteRunResult,
)


def _types_label(types: list) -> str:
    return " | ".join(t.value if hasattr(t, "value") else str(t) for t in types)


def _format_expected_item(item: ExpectedFindingResult) -> list[str]:
    lines = [
        f"{item.index}. `{_types_label(item.acceptable_types)}` — {item.description}",
        f"   - Status: **{'CAUGHT' if item.caught else 'MISSED'}**",
    ]
    if item.caught:
        lines.append(f"   - Matched finding: `{item.matched_finding_type}` — {item.matched_title}")
        if item.match_score is not None:
            lines.append(f"   - Match score: {item.match_score}")
    return lines


def _format_suite(suite: SuiteRunResult) -> list[str]:
    lines = [
        f"## {suite.suite_name}",
        "",
        f"- Suite id: `{suite.suite_id}`",
        f"- Target: `{suite.target_filename}` ({suite.target_doc_type.value})",
        f"- Recall: **{suite.recall_pct}%** ({suite.caught_count}/{suite.expected_count} caught)",
        f"- Actual findings: {suite.actual_finding_count} · Extra (not in answer key): {suite.extra_finding_count}",
    ]
    if suite.duration_ms is not None:
        lines.append(f"- Duration: {suite.duration_ms}ms")
    if suite.error_message:
        lines.append(f"- Error: {suite.error_message}")
    lines.append("")

    missed = [item for item in suite.expected_results if not item.caught]
    caught = [item for item in suite.expected_results if item.caught]

    lines.append(f"### Missed answer-key items ({len(missed)})")
    lines.append("")
    if missed:
        for item in missed:
            lines.extend(_format_expected_item(item))
            lines.append("")
    else:
        lines.append("_None — full recall on this suite._")
        lines.append("")

    lines.append(f"### Caught answer-key items ({len(caught)})")
    lines.append("")
    if caught:
        for item in caught:
            lines.extend(_format_expected_item(item))
            lines.append("")
    else:
        lines.append("_None._")
        lines.append("")

    lines.append(f"### Extra findings ({len(suite.extra_findings)})")
    lines.append("")
    lines.append("_Findings emitted by the linter but not matched to any answer-key item._")
    lines.append("")
    if suite.extra_findings:
        for index, finding in enumerate(suite.extra_findings, start=1):
            lines.append(f"{index}. `{finding.finding_type.value}` — **{finding.title}**")
            lines.append(f"   - {finding.message}")
            lines.append("")
    else:
        lines.append("_None._")
        lines.append("")

    return lines


def render_harness_run_markdown(detail: HarnessRunDetail) -> str:
    lines = [
        "# DeliveryLint Harness Run Report",
        "",
        "Use this report to improve lint rules, matching, or LLM extraction. "
        "Focus on **MISSED** items first — those are injected defects the answer key "
        "expects but the run did not catch.",
        "",
        "## Run summary",
        "",
        f"- Run id: {detail.id}",
        f"- Created: {detail.created_at.isoformat()}",
        f"- Status: `{detail.status.value}`",
        f"- LLM provider: `{detail.llm_provider}`",
        f"- Suites: {detail.suite_count}",
        f"- Overall recall: **{detail.recall_pct}%** "
        f"({detail.total_caught}/{detail.total_expected} caught, {detail.missed_count} missed)",
    ]
    if detail.error_message:
        lines.append(f"- Error: {detail.error_message}")
    lines.append("")

    if detail.status == HarnessRunStatus.RUNNING:
        lines.append("_Run still in progress — export again when complete._")
        return "\n".join(lines)

    if not detail.suite_results:
        lines.append("_No suite results recorded._")
        return "\n".join(lines)

    lines.append("## Suites")
    lines.append("")
    for suite in detail.suite_results:
        lines.extend(_format_suite(suite))

    lines.append("## Improvement checklist")
    lines.append("")
    lines.append("For each **MISSED** item above, consider:")
    lines.append("")
    lines.append("1. Was the target claim extracted by the target parser?")
    lines.append("2. Was the supporting reference fact extracted with correct status/authority?")
    lines.append("3. Does an existing lint rule cover this finding type?")
    lines.append("4. Is the scorer matching too strictly, or is the rule genuinely not firing?")
    lines.append("")

    return "\n".join(lines)


def export_filename(run_id: int) -> str:
    return f"deliverylint-harness-run-{run_id}.md"
