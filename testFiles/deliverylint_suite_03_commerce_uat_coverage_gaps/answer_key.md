# Answer Key — Suite 03 Commerce UAT Coverage Gaps

Target: `target_uat_plan.md`
Target doc type: `UAT_PLAN`

## Injected Findings

1. `missing_date_value` — UAT window uses “early May” and “before launch” instead of concrete dates from signed SOW: 2026-05-05 and 2026-05-16.
2. `reference_contradiction` — Target says Auctor executes UAT; signed SOW says RetailCo owns UAT execution.
3. `uat_test_missing_expected_result` — UAT-002 has an empty expected result.
4. `reference_contradiction` — UAT-003 uses $750 threshold and automatic approval for $700; signed SOW and requirements require Finance approval for refunds greater than $500.
5. `unresolved_reference_conflict` or `status_authority_mismatch` — Meeting notes discuss $750 as an idea but explicitly no decision/change order; target adopts $750-like behavior.
6. `reference_contradiction` — UAT-004 tests international returns as successful, but signed SOW explicitly excludes international returns.
7. `vague_requirement` — “quickly,” “easily,” “work properly,” and “as needed” are vague.
8. `uat_coverage_gap` — REQ-RET-003 exchange replacement order after warehouse receipt has no matching UAT test.
9. `uat_coverage_gap` — REQ-RET-005 Finance approval above $500 has no valid matching UAT test because the target test uses the wrong threshold and expected behavior.
10. `missing_acceptance_criteria` — Acceptance criteria are generic and do not verify required details such as RMA fields, 15-minute Zendesk update, warehouse receipt trigger, or Finance approval pending state.
