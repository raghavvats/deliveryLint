# target_draft_sow.md
Document type: DRAFT_SOW
Status: draft
Origin: Auctor Systems
Project: Northstar Components Salesforce CPQ Implementation

## 1. Overview

This draft Statement of Work describes the planned implementation services for Auctor Systems to configure Salesforce CPQ for Northstar Components, a mid-market manufacturer of custom industrial assemblies and replacement parts. Northstar is replacing spreadsheet-based quoting and disconnected approval processes with a governed Salesforce CPQ solution that supports product configuration, price calculation, discount approval, and quote document generation.

The project will support Northstar’s inside sales, regional account executives, sales operations, finance reviewers, and sales leadership. The implementation is expected to improve quote consistency, reduce manual calculation errors, and create a more seamless experience for sellers and approvers.

Auctor Systems will lead discovery validation, Salesforce CPQ configuration, quote template setup, approvals, user acceptance support, training, deployment support, and post-go-live stabilization. Northstar will provide timely access to subject matter experts, current pricing and product materials, and required systems.

## 2. In-Scope Services

Auctor Systems will provide the following services:

1. Salesforce CPQ configuration for Northstar’s standard manufactured components, configurable assemblies, replacement kits, and service add-ons.
2. Product catalog setup for approximately 850 active SKUs and up to 40 product bundles.
3. Price book configuration for list pricing, customer-specific pricing, and volume discounting.
4. Guided selling configuration to help users identify compatible products and required accessories.
5. Discount approval workflow for non-standard discounts and margin exceptions.
6. Quote document template configuration for customer-facing quote PDFs.
7. Account and opportunity field updates required to support CPQ quoting.
8. Migration of active quote templates and approved pricing rules from Northstar’s existing spreadsheets.
9. Integration with Salesforce Sales Cloud objects including Account, Opportunity, Product, Price Book, Quote, Quote Line, and Contract.
10. NetSuite billing sync for approved quotes, including transmission of customer, quote total, product line, tax category, and billing schedule information from Salesforce CPQ to NetSuite.
11. Customer portal quote acceptance so distributors can review and accept quotes online before order creation.
12. Project management, sprint planning, weekly status reporting, and cutover coordination.
13. Administrator enablement and end-user training.

The CPQ solution should be fast, user-friendly, and seamless for Northstar’s sales users. The final configuration should make it easy for users to build accurate quotes and should minimize manual work wherever possible.

## 3. Project Timeline

The project will run from May 18, 2026 through August 15, 2026, with production go-live targeted for August 15, 2026. The draft timeline is as follows:

| Phase | Dates | Summary |
|---|---:|---|
| Mobilization and access | May 18 - May 22, 2026 | Confirm project team, access, environments, and kickoff materials. |
| Discovery validation | May 26 - June 5, 2026 | Review product catalog, pricing, approval requirements, and quote templates. |
| Configuration sprint 1 | June 8 - June 26, 2026 | Configure core product catalog, bundles, and price books. |
| Configuration sprint 2 | June 29 - July 17, 2026 | Configure guided selling, approval rules, quote templates, and NetSuite billing sync. |
| UAT support | July 20 - July 31, 2026 | Support UAT execution and issue remediation. |
| Training and cutover | August 3 - August 14, 2026 | Deliver training, complete deployment readiness, and finalize cutover. |
| Go-live | August 15, 2026 | Production launch and hypercare start. |

## 4. Deliverables

Auctor Systems will produce the following deliverables:

| Deliverable | Description | Owner |
|---|---|---|
| Project kickoff deck | Project objectives, team, governance, and timeline. | Auctor Systems |
| Validated CPQ design summary | Summary of confirmed CPQ design choices, pricing logic, approvals, and quote template approach. | Auctor Systems |
| Configured Salesforce CPQ solution | Salesforce CPQ configuration for products, bundles, rules, pricing, approvals, and quote templates. | Auctor Systems |
| NetSuite billing integration design | Design and field mapping for NetSuite billing sync. | Auctor Systems |
| Customer portal quote acceptance prototype | Prototype portal allowing distributors to accept quotes online. | Auctor Systems |
| UAT support log | Defect triage log, issue status, and remediation notes during UAT. | Joint |
| Training materials | Admin and end-user training materials. | Auctor Systems |
| Deployment checklist | Cutover steps, validation activities, and rollback notes. | Auctor Systems |
| Hypercare summary | Summary of post-go-live issues, resolutions, and recommended next steps. | Auctor Systems |

## 5. Assumptions and Dependencies

The project assumes the following:

- Northstar will provide access to Salesforce sandbox and production environments.
- Northstar will provide complete SKU, product hierarchy, list pricing, discount matrix, and quote template inputs by May 29, 2026.
- Northstar will provide NetSuite sandbox access and API credentials by June 19, 2026.
- Northstar will identify UAT participants from sales operations, inside sales, finance, and sales leadership.
- Northstar will make business decisions within two business days where open questions affect configuration progress.
- Auctor Systems will have access to a Northstar Salesforce system administrator for configuration review and deployment support.
- Any third-party licensing required for CPQ, integrations, middleware, document generation, or customer portal functionality will be procured by Northstar.

## 6. Roles and Responsibilities

### Auctor Systems Responsibilities

Auctor Systems will:

- Manage the implementation plan and weekly status reporting.
- Configure Salesforce CPQ products, bundles, price rules, product rules, quote templates, and approval flows.
- Define and execute all UAT test scripts on behalf of Northstar business users.
- Prepare training materials and conduct two live training sessions.
- Support deployment planning and production cutover.
- Provide hypercare support for two weeks after go-live.

### Northstar Responsibilities

Northstar will:

- Provide project sponsorship and business owner participation.
- Provide approved product, pricing, discount, and template source materials.
- Review and approve configuration decisions.
- Provide Salesforce and NetSuite access.
- Provide a production-ready Salesforce CPQ managed package installation.
- Participate in weekly project meetings.

## 7. Acceptance Criteria

The project will be considered accepted when:

1. Salesforce CPQ is configured in production for Northstar’s approved product catalog and price books.
2. Sales users can create quotes using configured products, bundles, and guided selling prompts.
3. Discount approvals route to the appropriate approval group.
4. Quote PDFs are generated using the approved Northstar quote template.
5. NetSuite billing sync successfully sends approved quote data from Salesforce CPQ to NetSuite in test and production environments.
6. Customer portal quote acceptance is demonstrated to Northstar stakeholders.
7. UAT issues classified as critical or high are resolved or have an approved workaround.
8. Training materials have been delivered.

For user experience, the system should be fast and intuitive enough for sellers to use without confusion. The implementation team will evaluate this during UAT based on general feedback from pilot users.

## 8. Out-of-Scope Items

The following items are not planned for the first release unless mutually agreed during delivery:

- Large-scale historical quote migration.
- Complex tax calculation changes.
- Major redesign of Sales Cloud opportunity management.
- Custom manufacturing execution system changes.
- Any additional integrations not required for the CPQ launch.

## 9. Change Control

Changes identified during the project will be documented in the weekly status report and assessed for timeline, cost, and risk impact. Items that can be accommodated within the planned implementation effort may be incorporated into the active sprint backlog with agreement from the project team. Larger items may be scheduled for a later release.

## 10. Risks

Known risks include incomplete pricing source data, delayed business decisions, limited UAT participation, and environment access delays. NetSuite availability is also a dependency for billing sync testing. Auctor Systems and Northstar will review risks weekly and identify mitigation steps.
