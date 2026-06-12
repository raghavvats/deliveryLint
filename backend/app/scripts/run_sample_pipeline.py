"""Run the sample E2E pipeline and print findings."""

import asyncio
import json

from backend.app.pipeline.run_pipeline import run_full_pipeline
from backend.app.schemas.enums import ReviewPriority


async def main() -> None:
    result = await run_full_pipeline(include_debug=False)
    response = result.correction_ui_response

    print("=== DeliveryLint Sample Pipeline ===\n")
    print(f"Project: {response.project_id}")
    print(f"Target: {response.target_document.filename} ({response.target_document.doc_type.value})")
    print(f"\nSummary: {response.summary.model_dump()}\n")

    for priority in ReviewPriority:
        group = [f for f in response.findings if f.priority == priority]
        if not group:
            continue
        print(f"--- {priority.value.upper()} ({len(group)}) ---")
        for finding in group:
            print(f"  [{finding.severity.value}] {finding.title} (conf={finding.confidence:.2f})")
            print(f"    {finding.message}")
            if finding.target_quote:
                print(f"    Target: {finding.target_quote[:120]}")
            if finding.reference_quotes:
                print(f"    Reference: {finding.reference_quotes[0][:120]}")
            print()

    if response.lint_warnings:
        print("--- LINT WARNINGS ---")
        for warning in response.lint_warnings:
            print(f"  [{warning.code.value}] {warning.message}")

    print("\n--- JSON (truncated) ---")
    print(json.dumps(response.model_dump(), indent=2, default=str)[:3000])


if __name__ == "__main__":
    asyncio.run(main())
