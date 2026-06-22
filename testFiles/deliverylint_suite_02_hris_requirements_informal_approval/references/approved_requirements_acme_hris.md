# Approved Requirements — Acme HR Onboarding Automation

Doc type: REQUIREMENTS_DOC
Origin: joint
Status: approved
Recency date: 2026-05-03

## Functional Requirements
REQ-HRIS-001: When a US full-time employee is marked hired in Workday, ServiceNow must create an onboarding case.
Acceptance criteria: Given a US full-time employee with start date and manager populated, when Workday sends the hire event, then ServiceNow creates one onboarding case within 30 minutes.

REQ-HRIS-002: The onboarding case must include task templates for IT equipment, payroll setup, and benefits enrollment.
Acceptance criteria: Given a created onboarding case, then exactly one task from each approved template appears on the case.

REQ-HRIS-003: ServiceNow must send reminder emails 7 days and 2 days before the employee start date for incomplete onboarding tasks.
Acceptance criteria: Given incomplete tasks, reminder emails are sent on the configured schedule to the task owner.

REQ-HRIS-004: HR admins must be able to manually reassign onboarding tasks.
Acceptance criteria: Given an HR admin views an onboarding case, they can reassign a task and the audit log records the reassignment.

## Systems
- Workday
- ServiceNow HR Service Delivery
- Acme SSO

## Dependencies
- Acme must approve Workday field mapping by 2026-05-17.
- Acme Security must approve SSO by 2026-06-03.

## Open Questions
- Whether the IT task template should include a laptop-size field remains open.
