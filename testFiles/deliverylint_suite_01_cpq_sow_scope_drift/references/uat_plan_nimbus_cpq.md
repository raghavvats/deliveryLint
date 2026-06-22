# UAT Plan — Nimbus Fitness CPQ Phase 1

Doc type: UAT_PLAN
Origin: joint
Status: approved
Recency date: 2026-06-01

## Test Cases
UAT-001: Guided selling recommends the correct Treadmill bundle when a rep selects commercial gym, high durability, and subscription service.
Expected result: The recommended bundle includes the Treadmill Pro SKU and service subscription SKU.

UAT-002: A 20% discount quote is submitted.
Expected result: Approval is routed to Sales Operations and the rep cannot generate the final quote until approval is granted.

UAT-003: A North America quote PDF is generated.
Expected result: The PDF contains approved North America legal terms and Nimbus branding.

UAT-004: Nightly NetSuite export runs at 11:00 PM Eastern.
Expected result: The export file contains required billing fields and is available on the SFTP server by 7:00 AM Eastern.
