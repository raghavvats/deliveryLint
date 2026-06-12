"""Deterministic authority level computation."""

from backend.app.config.authority_config import AUTHORITY_DOWNGRADE_FLAGS
from backend.app.schemas.enums import DocType, ReliabilityFlag, SourceOrigin, SourceStatus


def compute_authority_level(
    doc_type: DocType,
    origin: SourceOrigin,
    status: SourceStatus,
    reliability_flags: list[ReliabilityFlag],
) -> int:
    del origin  # reserved for future rules

    if status == SourceStatus.SIGNED:
        level = 5
    elif doc_type == DocType.CHANGE_ORDER and status == SourceStatus.APPROVED:
        level = 5
    elif status == SourceStatus.APPROVED:
        level = 4
    elif doc_type == DocType.SIGNED_SOW:
        level = 5
    elif doc_type in {
        DocType.PROJECT_PLAN,
        DocType.STATUS_REPORT,
        DocType.CLIENT_EMAIL,
        DocType.MEETING_TRANSCRIPT,
    }:
        level = 3
    elif status in {SourceStatus.DRAFT, SourceStatus.INFORMAL}:
        level = 2
    else:
        level = 1

    if any(flag in reliability_flags for flag in AUTHORITY_DOWNGRADE_FLAGS):
        level = max(1, level - 1)

    return level


def build_authority_rationale(
    doc_type: DocType,
    status: SourceStatus,
    authority_level: int,
) -> str:
    if authority_level == 5:
        return (
            f"{doc_type.value} with status '{status.value}' is treated as a "
            "high-authority source for official project terms."
        )

    if authority_level == 4:
        return (
            f"{doc_type.value} with status '{status.value}' is treated as an "
            "approved source, but not necessarily a signed contractual source."
        )

    if authority_level == 3:
        return (
            f"{doc_type.value} is useful project evidence, but may not override "
            "signed or approved scope documents."
        )

    if authority_level == 2:
        return (
            f"{doc_type.value} with status '{status.value}' is lower-authority "
            "and should be treated cautiously."
        )

    return (
        f"{doc_type.value} has low or uncertain authority and should be used "
        "only as weak supporting context."
    )
