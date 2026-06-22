# UAT Plan — RetailCo Returns Portal

Doc type: UAT_PLAN
Status: draft

## UAT Window
UAT will start in early May and should finish before launch.
RetailCo Support will execute UAT with help from Auctor as needed.

## Test Cases

### UAT-001: Shopify customer initiates return
Steps:
1. Customer opens Shopify order history.
2. Customer selects a delivered order.
3. Customer clicks Return.
Expected result: Return request is created.

### UAT-002: NetSuite RMA creation
Steps:
1. Submit a Shopify return request.
2. Check NetSuite.
Expected result:

### UAT-003: Refund approval above $750
Steps:
1. Submit a refund request for $700.
2. Confirm the request does not require Finance approval.
Expected result: The refund is approved automatically.

### UAT-004: International return
Steps:
1. Submit a return for a Canadian order.
Expected result: The portal handles it successfully.

### UAT-005: Zendesk support visibility
Steps:
1. Open a Zendesk ticket for a customer with a pending return.
2. Verify return status is visible.
Expected result: Agent can see status quickly.

## Acceptance Criteria
- Customers can start returns easily.
- RMAs appear in NetSuite.
- Refund approvals work properly.
- Support can see statuses.

## Dates and Owners
- UAT start: early May
- UAT complete: before launch
- Environment setup: Auctor
- UAT execution: Auctor
