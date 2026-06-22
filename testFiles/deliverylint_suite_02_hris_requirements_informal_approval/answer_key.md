# Answer Key — Suite 02 HRIS Requirements Informal Approval

Target: `target_requirements_doc.md`
Target doc type: `REQUIREMENTS_DOC`

## Injected Findings

1. `reference_contradiction` — REQ-001 includes contractors and international employees; signed SOW explicitly limits scope to US full-time employees and excludes contractor/international onboarding.
2. `status_authority_mismatch` — Contractor onboarding appears as a requirement, but only a draft, unsigned change order proposes it.
3. `reference_contradiction` — REQ-002 says Workday sync must be real time; approved requirement only requires onboarding case creation within 30 minutes.
4. `reference_contradiction` — REQ-003 adds Slack provisioning; signed SOW excludes Slack workflow automation and client email asks for cost before inclusion.
5. `reference_contradiction` — REQ-003 adds background check tasks; signed SOW excludes background check vendor integration.
6. `reference_contradiction` — REQ-007 adds mobile onboarding app; signed SOW excludes mobile app development.
7. `unsupported_target_claim` — `BackgroundCheckPro` system is named but no reference supports this vendor/system.
8. `unsupported_target_claim` — “Mobile onboarding app” system is named but no reference supports a mobile app.
9. `vague_requirement` — “simple and seamless way to monitor onboarding progress” is vague.
10. `missing_acceptance_criteria` — REQ-001, REQ-002, REQ-003, REQ-004, REQ-006, and REQ-007 lack specific matching acceptance criteria.
11. `missing_date_value` — Dependencies say “before build completion” and “is needed” but omit concrete dates from references: field mapping by 2026-05-17 and SSO by 2026-06-03 / risk date 2026-06-14.
12. `reference_contradiction` — Open Questions says “None,” but approved requirements still list laptop-size field as open and status report lists SSO approval as blocked.
