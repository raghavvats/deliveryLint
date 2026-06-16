# reference_requirements_doc.md
Document type: REQUIREMENTS_DOC
Status: approved
Origin: joint
Project: Northstar Components Salesforce CPQ Implementation
Approved date: June 5, 2026

## 1. Purpose

This approved requirements document defines the functional and acceptance requirements for Northstar Components' first-release Salesforce CPQ implementation. Requirements are limited to Salesforce CPQ and Salesforce Sales Cloud configuration needed to support quoting. NetSuite billing, ERP order creation, customer portal acceptance, and other integrations are excluded from this approved release.

## 2. Systems

| System | Role in Release 1 | Notes |
|---|---|---|
| Salesforce Sales Cloud | Source CRM for Account, Opportunity, Product, Price Book, Quote, Quote Line, and Contract records | In scope |
| Salesforce CPQ | Primary quoting, configuration, pricing, approvals, and quote document generation system | In scope |
| NetSuite | ERP and billing system | Reference only; no integration in Release 1 |
| Excel pricing spreadsheets | Source reference for product and pricing inputs | Used for migration/reference; not a production system |

## 3. Requirements

| ID | Requirement | Priority | Owner | Acceptance Criteria |
|---|---|---|---|---|
| REQ-001 | Configure approximately 850 active products in Salesforce CPQ using Northstar's approved product master. | Must | Auctor Systems | Products load in sandbox and production with SKU, product family, active status, and list price where provided. |
| REQ-002 | Configure up to 40 product bundles for standard assemblies and service kits. | Must | Auctor Systems | Bundle selection displays required components and optional accessories for approved bundle list. |
| REQ-003 | Enforce required accessory rules and incompatibility rules for standard product families. | Must | Auctor Systems | Users cannot save a quote line combination that violates an approved incompatibility or missing-required-accessory rule. |
| REQ-004 | Configure standard list pricing, customer-specific pricing, and approved volume discount tiers. | Must | Auctor Systems | Representative test quotes calculate expected prices within $0.01 of approved pricing spreadsheet outputs. |
| REQ-005 | Configure discount approval routing for quote-level discount thresholds and margin exceptions. | Must | Auctor Systems | Quotes exceeding approved thresholds route to the correct sales manager or finance approver. |
| REQ-006 | Generate one approved customer-facing quote PDF template. | Must | Auctor Systems | Quote PDF includes customer, opportunity, quote number, quote expiration, line items, totals, terms, and approval status. |
| REQ-007 | Support guided selling prompts for standard product families. | Should | Auctor Systems | Users can answer guided questions and receive filtered product recommendations for at least three agreed product families. |
| REQ-008 | Preserve Sales Cloud opportunity linkage for all CPQ quotes. | Must | Auctor Systems | Each generated quote is associated with an Opportunity and Account and can be reported by opportunity owner. |
| REQ-009 | Provide UAT support for Northstar-owned UAT execution. | Must | Joint | UAT defects are logged with severity, owner, status, and resolution or approved workaround. |
| REQ-010 | Provide training materials for administrators and end users. | Must | Auctor Systems | Admin guide and end-user quick reference are delivered before training sessions. |
| REQ-011 | Execute production deployment and smoke testing. | Must | Joint | Production smoke test confirms create quote, configure bundle, calculate pricing, submit approval, and generate quote PDF. |
| REQ-012 | Exclude NetSuite billing sync and ERP posting from Release 1. | Must | Joint | No Salesforce-to-NetSuite billing, invoice, order, or ERP integration is configured or tested in Release 1. |
| REQ-013 | Exclude customer portal quote acceptance from Release 1. | Must | Joint | No distributor portal, customer portal, online acceptance, or self-service quote acceptance capability is configured. |

## 4. Non-Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|---|---|---|---|
| NFR-001 | Quote calculation performance for representative UAT quotes. | Should | For representative UAT scenarios with up to 75 quote lines, recalculation completes within 10 seconds in sandbox under normal test conditions. |
| NFR-002 | Usability for guided selling and quote generation. | Should | At least 80% of UAT participants can complete assigned quote creation tests using training materials without administrator intervention. |
| NFR-003 | Security and access. | Must | CPQ permissions are assigned only to named sales, sales operations, finance approval, and admin users identified by Northstar. |

## 5. Client Responsibilities

Northstar is responsible for:

- Providing approved product, pricing, discount, and bundle source data.
- Providing existing quote template and terms content.
- Reviewing and approving CPQ design decisions.
- Executing UAT test scripts and recording actual results.
- Verifying Salesforce CPQ licenses and environment access.
- Approving production deployment.

## 6. Implementation Team Responsibilities

Auctor Systems is responsible for:

- Configuring Salesforce CPQ for approved requirements.
- Preparing CPQ design documentation and training materials.
- Supporting UAT execution through defect triage and remediation.
- Preparing deployment checklist and supporting cutover.
- Providing hypercare support for two weeks after go-live.

## 7. Approved Exclusions

The approved requirements exclude NetSuite billing sync, invoice generation, order posting, middleware, customer portal quote acceptance, e-signature, historical quote migration, tax engine integration, manufacturing execution changes, and custom Lightning Web Components unless separately approved through written change control.
