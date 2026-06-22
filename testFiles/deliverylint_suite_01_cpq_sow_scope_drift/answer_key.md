# Answer Key — Suite 01 CPQ SOW Scope Drift

Target: `target_draft_sow.md`
Target doc type: `DRAFT_SOW`

## Injected Findings

1. `reference_contradiction` — Target includes Accessories in guided selling, but signed SOW limits guided selling to Treadmills, Bikes, and Rowers.
2. `reference_contradiction` — Target includes EMEA rollout/templates, but signed SOW explicitly limits phase 1 to North America and meeting notes confirm North America only.
3. `reference_contradiction` — Target includes SAP integration, but signed SOW and meeting notes explicitly mark SAP integration out of scope.
4. `reference_contradiction` — Target includes real-time two-way NetSuite synchronization, but signed SOW says one-way nightly export and explicitly excludes real-time NetSuite synchronization.
5. `status_authority_mismatch` — Target uses 10% discount threshold as if approved, but the client email only asks to explore 10% and explicitly says not to change configuration yet; signed/approved references say 15%.
6. `reference_contradiction` — Configuration sprint 2 complete is 2026-07-17 in target, but signed SOW says 2026-07-10.
7. `reference_contradiction` — Production go-live is 2026-08-10 in target, but signed SOW says 2026-08-03.
8. `reference_contradiction` — Target assigns UAT execution to Auctor, but signed SOW says Nimbus owns UAT execution.
9. `reference_contradiction` — Target assigns price book cleanup and production credentials to Auctor, but signed SOW says Nimbus owns final price book export and production credentials.
10. `reference_contradiction` — Target weakens change control by allowing weekly check-in changes without signed change order; signed SOW requires written signed change order before work begins.
11. `unsupported_target_claim` — Target says admin training for up to 12 users; signed SOW says up to 8 and no reference supports 12.
12. `vague_requirement` — “seamless CPQ performance,” “user-friendly admin experience,” “fast and intuitive,” and “as needed” are vague.
13. `missing_acceptance_criteria` — Target claims CPQ supports “all required selling motions” without concrete acceptance criteria.
14. `missing_date_value` — Dependencies say credentials/legal language are needed “before” phases, but no concrete date values are included.
