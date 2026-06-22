# Signed SOW — Nimbus Fitness Salesforce CPQ Phase 1

Doc type: SIGNED_SOW
Origin: joint
Status: signed
Recency date: 2026-05-12

## Parties
- Client: Nimbus Fitness, Inc.
- Vendor: Auctor Delivery Services

## In-Scope Work
1. Configure Salesforce CPQ guided selling for three product families: Treadmills, Bikes, and Rowers.
2. Configure approval rules for discounts greater than 15%.
3. Configure quote templates for the North America sales team only.
4. Implement a one-way nightly NetSuite billing export from Salesforce CPQ to NetSuite.
5. Migrate active price book entries from the existing CPQ sandbox into production.
6. Provide admin training for up to 8 Nimbus users.

## Explicitly Out of Scope
- SAP integration of any kind.
- Europe, Middle East, and Asia-Pacific rollout.
- Data migration for closed/lost opportunities.
- Custom mobile application work.
- Real-time NetSuite synchronization.
- Tax engine implementation.

## Milestones
| Milestone | Date | Owner |
|---|---:|---|
| Kickoff complete | 2026-06-03 | Joint |
| Configuration sprint 1 complete | 2026-06-26 | Auctor |
| Configuration sprint 2 complete | 2026-07-10 | Auctor |
| UAT complete | 2026-07-24 | Nimbus |
| Production go-live | 2026-08-03 | Joint |

## Responsibilities
- Auctor owns CPQ configuration, quote template configuration, and NetSuite export development.
- Nimbus owns timely review, business-rule approval, UAT execution, and production credentials.
- Nimbus is responsible for providing final price book export by 2026-06-07.

## Change Control
Any change to scope, timeline, fees, integrations, regions, or data migration requires a written change order signed by both parties before work begins.

## Acceptance Criteria
- Guided selling rules produce the correct bundle recommendations for Treadmills, Bikes, and Rowers.
- Discount approvals route to the Sales Operations queue when discount is greater than 15%.
- Quote PDFs use the approved North America legal language.
- NetSuite export file is generated nightly and contains account, quote, product, quantity, price, and billing-start-date fields.
