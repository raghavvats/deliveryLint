# Answer Key — Suite 04 EHR Project Plan Owner and Date Conflicts

Target: `target_project_plan.md`
Target doc type: `PROJECT_PLAN`

## Injected Findings

1. `missing_date_value` — Epic build workbook approval uses “week of March 10” instead of concrete date.
2. `reference_contradiction` — Epic build workbook approval owner is Auctor in target; signed SOW says ValleyCare owns it.
3. `reference_contradiction` — ClearingHub test file owner is Auctor in target; signed SOW says ValleyCare owns ClearingHub coordination/test file.
4. `reference_contradiction` — ClearingHub test file date is 2026-03-28; signed SOW says 2026-03-20 and status report says it was not received as of 2026-03-18.
5. `reference_contradiction` — Rules engine configured date is 2026-04-17; signed SOW and baseline project plan say 2026-04-10.
6. `reference_contradiction` — Rules engine configured owner is ValleyCare; signed SOW says Auctor owns rules engine configuration.
7. `reference_contradiction` — Integrated testing complete date is 2026-04-30; signed SOW says 2026-04-24.
8. `reference_contradiction` — Integrated testing owner is Auctor; signed SOW says Joint.
9. `reference_contradiction` — Training complete owner is ValleyCare; signed SOW says Auctor owns training/training materials.
10. `reference_contradiction` — Go-live date is 2026-05-13; signed SOW says 2026-05-06.
11. `reference_contradiction` — Target includes oncology workflows; signed SOW and status report exclude oncology, and client email is only an informal request.
12. `status_authority_mismatch` — Oncology is treated as included even though only an informal client email requested it and asked whether a change order is needed.
13. `reference_contradiction` — Target says replacement Epic workqueues; signed SOW explicitly excludes replacing Epic workqueues.
14. `reference_contradiction` — Auctor coordinates HIPAA review; signed SOW says ValleyCare Compliance owns HIPAA review.
15. `missing_date_value` — Dependencies use “before configuration starts,” “before go-live,” and “soon” without concrete dates.
16. `reference_contradiction` — Status update says ClearingHub file received; status report says it had not been received as of 2026-03-18.
17. `unsupported_target_claim` — “Minor dependency delays can be absorbed without timeline impact” is not supported and conflicts with risk notes that delays may push validation.
18. `vague_requirement` — “as needed,” “soon,” and “work efficiently” are vague.
