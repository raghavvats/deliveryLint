from backend.app.domain.authority import compute_authority_level
from backend.app.schemas.enums import DocType, SourceOrigin, SourceStatus


def test_signed_sow_authority() -> None:
    level = compute_authority_level(
        DocType.SIGNED_SOW,
        SourceOrigin.JOINT,
        SourceStatus.SIGNED,
        [],
    )
    assert level == 5
