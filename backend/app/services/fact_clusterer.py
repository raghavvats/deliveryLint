"""Fact clustering service."""

from uuid import uuid4

from backend.app.schemas.enums import ClusterResolutionStatus, FactPolarity
from backend.app.schemas.fact_cluster import FactCluster
from backend.app.schemas.project_fact import ProjectFact


def detect_cluster_conflicts(
    cluster: FactCluster,
    facts: list[ProjectFact],
) -> ClusterResolutionStatus:
    fact_by_id = {fact.id: fact for fact in facts}
    polarities: set[FactPolarity] = set()
    for fact_id in cluster.fact_ids:
        fact = fact_by_id.get(fact_id)
        if fact:
            polarities.add(fact.polarity)

    if FactPolarity.POSITIVE in polarities and FactPolarity.NEGATIVE in polarities:
        return ClusterResolutionStatus.CONFLICT
    if len(polarities) > 1:
        return ClusterResolutionStatus.UNRESOLVED
    return ClusterResolutionStatus.CONSISTENT


def _select_dominant_polarity(facts: list[ProjectFact]) -> FactPolarity:
    counts = {FactPolarity.POSITIVE: 0, FactPolarity.NEGATIVE: 0, FactPolarity.NEUTRAL: 0}
    for fact in facts:
        counts[fact.polarity] += 1
    return max(counts, key=counts.get)


def _select_canonical_fact_id(facts: list[ProjectFact]) -> str | None:
    if not facts:
        return None
    sorted_facts = sorted(
        facts,
        key=lambda f: (f.source_authority_level, f.extraction_confidence),
        reverse=True,
    )
    return sorted_facts[0].id


def cluster_facts(facts: list[ProjectFact]) -> list[FactCluster]:
    groups: dict[str, list[ProjectFact]] = {}
    for fact in facts:
        groups.setdefault(fact.normalized_subject, []).append(fact)

    clusters: list[FactCluster] = []
    for normalized_subject, group_facts in groups.items():
        dominant_polarity = _select_dominant_polarity(group_facts)
        fact_ids = [fact.id for fact in group_facts]
        cluster = FactCluster(
            id=f"cluster_{uuid4().hex}",
            normalized_subject=normalized_subject,
            fact_ids=fact_ids,
            dominant_polarity=dominant_polarity,
            resolution_status=ClusterResolutionStatus.CONSISTENT,
            conflict_summary=None,
            canonical_fact_id=_select_canonical_fact_id(group_facts),
        )
        cluster.resolution_status = detect_cluster_conflicts(cluster, group_facts)
        if cluster.resolution_status == ClusterResolutionStatus.CONFLICT:
            cluster.conflict_summary = (
                f"Conflicting polarities for subject '{normalized_subject}'."
            )
        clusters.append(cluster)

    return clusters
