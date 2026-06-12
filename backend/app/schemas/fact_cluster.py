from pydantic import BaseModel, Field

from backend.app.schemas.enums import ClusterResolutionStatus, FactPolarity


class FactCluster(BaseModel):
    id: str
    normalized_subject: str
    fact_ids: list[str]
    dominant_polarity: FactPolarity
    resolution_status: ClusterResolutionStatus
    conflict_summary: str | None = None
    canonical_fact_id: str | None = None
