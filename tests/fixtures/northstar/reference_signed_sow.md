# reference_signed_sow.md
Document type: SIGNED_SOW
Status: signed
Origin: joint
Project: Northstar Components Salesforce CPQ Implementation
Effective date: May 15, 2026
Signed by: Northstar Components and Auctor Systems

## 1. Executive Summary

Northstar Components has engaged Auctor Systems to implement Salesforce CPQ for its core quoting process. Northstar manufactures configurable industrial components, replacement assemblies, and service kits sold through direct sales representatives and distributor channels. The current quoting process relies on spreadsheets, manual discount approvals, and inconsistent quote documents.

The objective of this project is to implement Salesforce CPQ for governed quote creation, product selection, price calculation, discount approval, and quote document generation. The first release is intentionally limited to Salesforce CPQ and Salesforce Sales Cloud configuration needed to support quoting. Billing, ERP order creation, tax engine replacement, customer portal capabilities, and manufacturing execution changes are not part of this signed scope.

This signed SOW is the controlling project document. In the event of conflict between this signed SOW and informal communications, meeting notes, draft documents, or unapproved requests, this signed SOW governs unless amended through written change control signed by both parties.

## 2. Official Scope

Auctor Systems will configure Salesforce CPQ in Northstar’s Salesforce environment for the following in-scope capabilities:

1. Product catalog and product hierarchy setup for approximately 850 active SKUs.
2. Configuration of up to 40 product bundles for standard assemblies and service kits.
3. Product rules for required accessories, incompatible selections, and basic validation messages.
4. Price book configuration for standard list pricing, customer-specific pricing, and approved volume discount tiers.
5. CPQ price rules for approved discount calculations and selected surcharge calculations.
6. Guided selling prompts for standard product families.
7. Discount approval workflows for quote-level discount thresholds and margin exception review.
8. Quote document generation using one approved Northstar customer-facing quote template.
9. Sales Cloud field updates required for CPQ operation on Account, Opportunity, Product, Price Book, Quote, Quote Line, and Contract objects.
10. Deployment support from sandbox to production.
11. UAT support, defect triage, training, and two weeks of post-go-live hypercare.

## 3. Explicitly Out-of-Scope Items

The following items are expressly excluded from this SOW and require a separate change order or future phase:

- NetSuite billing integration, billing sync, invoice creation, order creation, or ERP posting.
- Any middleware implementation, iPaaS configuration, or custom API integration between Salesforce and NetSuite.
- Customer portal, distributor portal, online quote acceptance, e-signature, or self-service ordering functionality.
- Historical quote migration beyond reference-only review of current quote templates and pricing spreadsheets.
- Tax engine replacement or tax calculation integration.
- Manufacturing execution system, inventory management, warehouse, fulfillment, or production scheduling changes.
- Custom Lightning Web Components unless approved by written change control.
- Data cleansing of Northstar’s product master or customer master beyond formatting source files for CPQ import.
- Third-party license procurement or subscription management.

## 4. Deliverables

The official deliverables are:

| ID | Deliverable | Description | Owner |
|---|---|---|---|
| D1 | Project kickoff deck | Project objectives, team roster, governance, communication cadence, scope, risks, and milestone plan. | Auctor Systems |
| D2 | CPQ design summary | Confirmed design for product catalog, bundles, product rules, price books, price rules, approvals, and quote template. | Auctor Systems |
| D3 | Configured Salesforce CPQ solution | Configuration in Northstar sandbox and production for in-scope CPQ capabilities. | Auctor Systems |
| D4 | Quote template configuration | One approved customer-facing quote PDF template configured in Salesforce CPQ. | Auctor Systems |
| D5 | UAT support log | Log of UAT issues, severity, status, owner, and resolution or approved workaround. | Joint |
| D6 | Training materials | Admin guide and end-user quick reference materials. | Auctor Systems |
| D7 | Deployment checklist | Cutover checklist, production validation steps, and rollback considerations. | Auctor Systems |
| D8 | Hypercare summary | Summary of post-go-live support items, resolutions, and open recommendations. | Auctor Systems |

No integration design, customer portal prototype, ERP billing sync deliverable, or custom order management deliverable is included in this SOW.

## 5. Project Timeline and Milestones

The official project dates are:

- Project kickoff: May 18, 2026
- Discovery validation complete: June 5, 2026
- Configuration sprint 1 complete: June 26, 2026
- Configuration sprint 2 complete: July 10, 2026
- UAT window: July 13, 2026 through July 24, 2026
- Training and cutover readiness: July 27, 2026 through July 31, 2026
- Production go-live: August 1, 2026
- Hypercare: August 3, 2026 through August 14, 2026

Any change to the production go-live date must be approved by the Northstar executive sponsor and Auctor engagement manager through change control.

## 6. Assumptions

This SOW assumes:

- Northstar has active Salesforce CPQ licenses for all in-scope users before configuration begins.
- Northstar will provide Salesforce sandbox and production access by May 20, 2026.
- Northstar will provide product, pricing, discount, bundle, and quote template source materials by May 29, 2026.
- Northstar will identify UAT participants by June 19, 2026.
- Northstar will assign one Salesforce administrator to support environment access, deployment review, and production validation.
- Auctor Systems will use declarative Salesforce CPQ configuration wherever possible.
- Northstar’s source product and pricing data is materially complete and approved by business owners.
- No NetSuite, ERP, billing, tax, portal, or middleware access is required for this first release.

## 7. Dependencies

Key dependencies include:

- Timely access to Northstar Salesforce sandbox and production environments.
- Timely delivery of approved product and pricing source materials.
- Business owner availability for design decisions and UAT execution.
- Northstar Salesforce administrator availability for package verification and deployment support.
- Northstar executive sponsor availability for scope or timeline decisions.

## 8. Responsibilities

### Auctor Systems Responsibilities

Auctor Systems will:

- Manage project delivery, sprint planning, status reporting, and risk tracking.
- Facilitate discovery validation and document confirmed CPQ design decisions.
- Configure in-scope Salesforce CPQ capabilities.
- Prepare deployment checklist and support production cutover.
- Provide UAT support, including defect triage and remediation for configuration defects.
- Provide training materials and conduct two remote training sessions.
- Provide two weeks of hypercare after go-live.

### Northstar Responsibilities

Northstar will:

- Provide executive sponsorship and business ownership.
- Provide source data, policies, approval thresholds, and quote template inputs.
- Make business decisions within two business days for questions affecting configuration.
- Install or verify the Salesforce CPQ managed package and ensure licenses are assigned.
- Provide Salesforce sandbox and production access.
- Own and execute UAT test scripts with support from Auctor Systems.
- Review and approve deliverables within three business days.
- Provide production deployment approval.

## 9. Acceptance Criteria

The project will be accepted when all of the following are true:

1. In-scope CPQ configuration is deployed to production.
2. Product catalog includes approximately 850 active SKUs provided by Northstar.
3. Up to 40 approved bundles are configured with required component and incompatibility rules.
4. Standard list pricing, customer-specific pricing, and approved volume discount tiers calculate correctly for representative UAT scenarios.
5. Discount approvals route based on approved thresholds and margin exception logic.
6. One approved quote PDF template generates with correct customer, opportunity, quote line, pricing, terms, and approval status fields.
7. Northstar completes UAT and signs off with no unresolved critical or high-severity defects.
8. Training materials and deployment checklist are delivered.
9. Production smoke test confirms that sales users can create, price, approve, and generate a quote document.

## 10. Change Control

Any requested change that affects scope, timeline, cost, deliverables, systems, integrations, or acceptance criteria must be documented in a change request. A change request is approved only when signed by the Northstar executive sponsor and the Auctor engagement manager. Informal emails, meeting discussion, backlog notes, and tentative ideas do not constitute approved scope.

## 11. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Product/pricing data is incomplete or inconsistent | Delays configuration and testing | Northstar to provide approved source files by May 29 and assign data owner. |
| UAT participants are unavailable | Defects may be found late | Northstar to name UAT users by June 19 and protect UAT time. |
| Approval thresholds are not finalized | Workflow may require rework | Sales operations and finance to approve thresholds during discovery validation. |
| Go-live date pressure compresses testing | Quality risk | Scope remains limited to CPQ first release; out-of-scope integrations deferred. |
