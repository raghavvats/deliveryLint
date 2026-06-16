# reference_uat_plan.md
Document type: UAT_PLAN
Status: approved
Origin: joint
Project: Northstar Components Salesforce CPQ Implementation
Approved date: July 8, 2026
UAT window: July 13, 2026 - July 24, 2026

## 1. Purpose

This UAT plan defines the approved user acceptance tests for the Salesforce CPQ Release 1 implementation. UAT will be executed by Northstar business users with support from Auctor Systems. The purpose is to confirm that Salesforce CPQ supports approved quoting requirements before the August 1, 2026 production go-live.

## 2. UAT Roles

| Role | Party | Responsibility |
|---|---|---|
| UAT Lead | Northstar Sales Operations | Coordinate testers, consolidate results, approve UAT completion. |
| Business Testers | Northstar sales, finance, sales leadership | Execute test scripts and record actual results. |
| Defect Triage Lead | Auctor Systems | Review defects, assign severity, recommend remediation. |
| Salesforce Admin | Northstar IT | Support access, permissions, and deployment validation. |

## 3. Entry Criteria

- CPQ configuration is complete in UAT sandbox.
- Product and pricing test data is loaded.
- UAT users have assigned permissions.
- Test scripts are distributed to testers.
- Known open configuration items are documented.

## 4. Exit Criteria

- All must-pass tests are executed.
- No unresolved critical or high-severity defects remain unless a workaround is approved by Northstar.
- UAT lead signs off on Release 1 readiness.
- Production smoke test plan is confirmed.

## 5. UAT Test Cases

| Test ID | Requirement IDs | Scenario | Steps Summary | Expected Result | Pass/Fail Owner |
|---|---|---|---|---|---|
| UAT-001 | REQ-001, REQ-008 | Create a quote for a standard active SKU from an Opportunity. | Open opportunity, create quote, add standard SKU, save. | Quote is linked to Account and Opportunity; active SKU is selectable; line price populates from approved price book. | Northstar Sales Ops |
| UAT-002 | REQ-002, REQ-003 | Configure a standard assembly bundle with required components. | Add assembly bundle, review required component selections, attempt save without required accessory. | Required accessory is displayed; quote cannot be saved until required accessory is selected. | Northstar Inside Sales |
| UAT-003 | REQ-003 | Validate incompatible product rule. | Add two products listed as incompatible in approved rules. | User receives clear validation message and cannot save the invalid combination. | Northstar Sales Ops |
| UAT-004 | REQ-004 | Validate list price and volume discount calculation. | Add approved SKU quantity at volume tier threshold; compare output to pricing spreadsheet. | Calculated price matches approved spreadsheet within $0.01. | Northstar Finance |
| UAT-005 | REQ-004 | Validate customer-specific pricing. | Create quote for customer with approved special price record. | Customer-specific price overrides standard list price according to approved rules. | Northstar Finance |
| UAT-006 | REQ-005 | Submit quote requiring sales manager approval. | Create quote above sales discount threshold and submit for approval. | Approval request routes to assigned sales manager group with quote details. | Northstar Sales Leadership |
| UAT-007 | REQ-005 | Submit quote requiring finance margin approval. | Create quote with margin exception and submit for approval. | Approval request routes to finance approver group and records approval status. | Northstar Finance |
| UAT-008 | REQ-006 | Generate customer-facing quote PDF. | Generate PDF for approved quote. | PDF includes customer, quote number, expiration date, line items, totals, terms, and approval status. | Northstar Sales Ops |
| UAT-009 | REQ-007, NFR-002 | Use guided selling for a standard product family. | Launch guided selling, answer prompts, select recommended product. | System filters options and recommends products for agreed product family; tester completes flow using quick reference. | Northstar Inside Sales |
| UAT-010 | NFR-001 | Recalculate representative 75-line quote. | Add or load representative 75-line quote and recalculate. | Recalculation completes within 10 seconds in sandbox under normal test conditions. | Northstar Sales Ops |
| UAT-011 | REQ-011 | Production smoke test rehearsal. | Perform create quote, configure bundle, calculate pricing, submit approval, generate PDF in sandbox. | All smoke test steps complete without critical or high-severity defects. | Joint |
| UAT-012 | REQ-012 | Confirm NetSuite billing sync is not part of Release 1 testing. | Review test scope and system behavior after quote approval. | No NetSuite billing sync, ERP posting, invoice creation, or order creation is configured or expected. | Northstar UAT Lead |
| UAT-013 | REQ-013 | Confirm customer portal quote acceptance is not part of Release 1 testing. | Review available user flows and portal-related functionality. | No distributor portal, customer portal, online quote acceptance, or self-service quote acceptance is configured or expected. | Northstar UAT Lead |

## 6. Defect Severity

| Severity | Definition | Resolution Requirement |
|---|---|---|
| Critical | Blocks core quote creation, pricing, approval, or PDF generation for must-pass flows. | Must be resolved before go-live. |
| High | Materially affects approved CPQ functionality but workaround may exist. | Resolve or obtain approved workaround before go-live. |
| Medium | Affects usability or edge-case behavior without blocking release. | Resolve before go-live where feasible or backlog with owner. |
| Low | Cosmetic or minor improvement. | Backlog or resolve as capacity allows. |

## 7. Out-of-Scope UAT Items

UAT will not test NetSuite billing sync, order creation, invoice creation, customer portal quote acceptance, e-signature, manufacturing execution, tax engine replacement, or historical quote migration.
