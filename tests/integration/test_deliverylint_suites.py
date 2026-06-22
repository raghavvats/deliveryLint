"""Integration tests for running benchmark suites through the pipeline."""

import os

import pytest

from backend.app.test_harness.runner import run_harness
from backend.app.test_harness.suite_loader import discover_suites


@pytest.mark.asyncio
async def test_harness_runs_all_suites_without_crashing() -> None:
    result = await run_harness()
    assert result.suite_count == len(discover_suites())
    assert result.total_expected > 0
    assert 0.0 <= result.recall_pct <= 100.0
    for suite in result.suite_results:
        assert suite.expected_count == len(
            next(item for item in discover_suites() if item.id == suite.suite_id).expected_findings
        )


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_HARNESS_RECALL_TESTS", "").lower() not in {"1", "true", "yes"},
    reason="Set RUN_HARNESS_RECALL_TESTS=1 with LLM_PROVIDER=openai for recall assertions",
)
async def test_harness_recall_nonzero_with_openai() -> None:
    if os.getenv("LLM_PROVIDER", "mock") != "openai":
        pytest.skip("Requires LLM_PROVIDER=openai")
    result = await run_harness(suite_ids=["deliverylint_suite_01_cpq_sow_scope_drift"])
    assert result.total_caught > 0
