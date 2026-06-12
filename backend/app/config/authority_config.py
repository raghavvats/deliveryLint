"""Authority downgrade flag configuration."""

from backend.app.schemas.enums import ReliabilityFlag

AUTHORITY_DOWNGRADE_FLAGS: set[ReliabilityFlag] = {
    ReliabilityFlag.LOW_DOC_TYPE_CONFIDENCE,
    ReliabilityFlag.LOW_STATUS_CONFIDENCE,
    ReliabilityFlag.UNKNOWN_SOURCE,
    ReliabilityFlag.INTERNAL_CONFLICTS,
    ReliabilityFlag.USER_LABEL_CONFLICTS_WITH_CONTENT,
}
