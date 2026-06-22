"""Run DeliveryLint benchmark suites from the command line."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from backend.app.db.models import save_test_harness_run
from backend.app.test_harness.runner import run_harness
from backend.app.test_harness.schemas import HarnessRunStatus
from backend.app.test_harness.suite_loader import discover_suites


def _print_summary(result) -> None:
    print(f"Harness run recall: {result.recall_pct}% ({result.total_caught}/{result.total_expected})")
    print(f"LLM provider: {result.llm_provider}")
    print(f"Suites: {result.suite_count}")
    print()
    for suite in result.suite_results:
        status = "OK" if suite.status == "completed" else "FAIL"
        print(
            f"[{status}] {suite.suite_id}: "
            f"{suite.recall_pct}% ({suite.caught_count}/{suite.expected_count}) "
            f"— {suite.actual_finding_count} findings, {suite.extra_finding_count} extra"
        )
        if suite.error_message:
            print(f"  error: {suite.error_message}")
        missed = [item for item in suite.expected_results if not item.caught]
        if missed:
            print(f"  missed ({len(missed)}):")
            for item in missed[:5]:
                types = " | ".join(t.value for t in item.acceptable_types)
                print(f"    #{item.index} [{types}] {item.description[:100]}")
            if len(missed) > 5:
                print(f"    ... and {len(missed) - 5} more")


async def _main_async(args: argparse.Namespace) -> int:
    suites = discover_suites()
    if args.list:
        for suite in suites:
            print(
                f"{suite.id}\t{suite.target_doc_type.value}\t"
                f"{len(suite.expected_findings)} expected\t{suite.target_filename}"
            )
        return 0

    suite_ids = args.suite or None
    result = await run_harness(suite_ids=suite_ids)

    if args.save:
        record = save_test_harness_run(
            result.model_dump_json(),
            status=result.status.value,
            llm_provider=result.llm_provider,
            error_message=result.error_message,
        )
        result.id = record.id

    if args.json:
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    else:
        _print_summary(result)

    if result.status == HarnessRunStatus.FAILED:
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run DeliveryLint benchmark test suites")
    parser.add_argument(
        "--suite",
        action="append",
        help="Run only the given suite id (repeatable). Default: all suites.",
    )
    parser.add_argument("--list", action="store_true", help="List available suites and exit")
    parser.add_argument("--json", action="store_true", help="Print full JSON result")
    parser.add_argument("--save", action="store_true", help="Persist result to the database")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_main_async(args)))


if __name__ == "__main__":
    main()
