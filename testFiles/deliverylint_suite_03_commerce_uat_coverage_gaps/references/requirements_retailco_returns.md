# Requirements — RetailCo Returns Portal

Doc type: REQUIREMENTS_DOC
Origin: joint
Status: approved
Recency date: 2026-03-30

## Functional Requirements
REQ-RET-001: Customers must be able to initiate a return from Shopify order history for delivered orders within 30 days of delivery.
Acceptance criteria: A delivered order within 30 days shows a Return button and creates a return request.

REQ-RET-002: Returns must create a Return Merchandise Authorization record in NetSuite.
Acceptance criteria: A submitted return request creates an RMA in NetSuite with order number, SKU, quantity, reason code, and customer email.

REQ-RET-003: Exchanges must create a replacement order in Shopify only after warehouse receipt is confirmed.
Acceptance criteria: When NetSuite marks the returned item received, Shopify creates a replacement order for the approved exchange SKU.

REQ-RET-004: Return status updates must be visible in Zendesk for support agents.
Acceptance criteria: A Zendesk agent viewing a ticket can see current return status within 15 minutes of status change.

REQ-RET-005: Refunds greater than $500 must require Finance approval.
Acceptance criteria: A refund request above $500 remains pending until Finance approves it.

## Systems
- Shopify Plus
- NetSuite
- Zendesk
- Warehouse API

## Dependencies
- RetailCo provides NetSuite sandbox access by 2026-04-08.
- RetailCo provides Warehouse API credentials by 2026-04-12.
