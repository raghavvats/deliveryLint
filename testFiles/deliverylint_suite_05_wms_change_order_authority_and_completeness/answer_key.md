# Answer Key — Suite 05 WMS Change Order Authority and Completeness

Target: `target_change_order.md`
Target doc type: `CHANGE_ORDER`
Target status: `draft`

## Injected Findings

1. `reference_contradiction` — Voice picking is included, but signed SOW explicitly excludes voice picking.
2. `status_authority_mismatch` — Voice picking is treated as included even though the client email only asks for pricing as a possible change order.
3. `reference_contradiction` — Labor management optimization is included, but signed SOW excludes labor management optimization and the approved change order excludes optimization recommendations.
4. `reference_contradiction` — Real-time SAP inventory updates are included, but signed SOW excludes real-time SAP integration and meeting notes confirm no change was approved.
5. `reference_contradiction` — Dallas DC rollout is included, but signed SOW excludes additional distribution centers beyond Chicago DC.
6. `status_authority_mismatch` — Shift scheduling dashboard is included, but approved change order excludes shift scheduling; status report says second dashboard view by shift is open and not approved.
7. `reference_contradiction` — Custom scanner headset procurement is included, but signed SOW excludes custom hardware procurement and says GlobalFoods owns scanner hardware.
8. `reference_contradiction` — Transportation management integration is included, but signed SOW explicitly excludes TMS integration.
9. `reference_contradiction` — Target says no go-live impact, but approved labor reporting change order already moves go-live from 2026-04-29 to 2026-05-06; additional listed changes have no supporting approved timeline.
10. `unsupported_target_claim` — “completed during the current phase without impacting the approved go-live date” has no support.
11. `reference_contradiction` — Target assigns UAT execution to Auctor; signed SOW says GlobalFoods owns UAT execution.
12. `reference_contradiction` — Target assigns scanner hardware procurement to Auctor; signed SOW says GlobalFoods owns scanner hardware.
13. `reference_contradiction` — Target assigns SAP basis support to Auctor; signed SOW says SAP integration testing requires GlobalFoods SAP basis support.
14. `missing_date_value` — Timeline has no concrete dates.
15. `missing_owner` — Dependencies “SAP access” and “Warehouse users” lack assigned owners.
16. `vague_requirement` — “easier to manage,” “straightforward,” “work seamlessly,” “quickly,” and “as needed” are vague.
17. `missing_acceptance_criteria` — Acceptance criteria are generic and do not define measurable results for voice picking, SAP sync, Dallas rollout, scheduling dashboard, or TMS integration.
18. `missing_expected_content` — As a change order, target is missing fee impact/cost section despite signed SOW change-control requirements requiring fee impact in signed change orders.
19. `missing_expected_content` — Target lacks explicit out-of-scope section for the change order.
