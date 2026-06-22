# Requirements — Nimbus Fitness CPQ Phase 1

Doc type: REQUIREMENTS_DOC
Origin: joint
Status: approved
Recency date: 2026-05-20

## Functional Requirements
REQ-CPQ-001: Sales reps must answer guided selling questions and receive recommended bundles for Treadmills, Bikes, and Rowers.
REQ-CPQ-002: Discounts greater than 15% must require Sales Operations approval.
REQ-CPQ-003: Quote documents must use approved North America terms and branding.
REQ-CPQ-004: A nightly NetSuite billing export must run at 11:00 PM Eastern and include account, quote, SKU, quantity, net price, and billing start date.
REQ-CPQ-005: Only active price book entries will be migrated.

## Non-Functional Requirements
NFR-CPQ-001: Nightly export completion must be visible in Salesforce by 7:00 AM Eastern the next business day.
NFR-CPQ-002: Admin users must be able to update guided selling question text without developer support.

## Dependencies
- Nimbus provides final price book export by 2026-06-07.
- Nimbus provides NetSuite SFTP credentials by 2026-06-14.
- Auctor receives final North America legal terms by 2026-06-12.

## Open Questions
- Whether Nimbus wants exception reporting for rejected NetSuite rows is open and not approved for phase 1.
