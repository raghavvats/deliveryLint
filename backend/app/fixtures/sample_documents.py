"""Sample raw document text for E2E pipeline."""

SIGNED_SOW_TEXT = """
Statement of Work - Salesforce CPQ Implementation

Out of scope: NetSuite billing integration and custom tax logic.

Scope includes Salesforce CPQ configuration, quote templates, and discount approval routing.

Go-live date: August 1, 2026.

Client will provide product master data by June 15, 2026.
"""

CLIENT_EMAIL_TEXT = """
Subject: NetSuite billing sync

Can we also add NetSuite billing sync before launch?
"""

DRAFT_SOW_TARGET_TEXT = """
Draft Statement of Work

Scope of Work
The implementation will include NetSuite billing integration before go-live.
Salesforce CPQ configuration and quote template setup are included.

Deliverables
- Configured CPQ instance
- Quote approval workflow

Timeline
Go-live target: August 15, 2026.
"""

PROJECT_ID = "project_001"

SIGNED_SOW_DOC_ID = "doc_signed_sow"
CLIENT_EMAIL_DOC_ID = "doc_client_email"
TARGET_DOC_ID = "doc_target_draft_sow"
