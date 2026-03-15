"""Scorecard service for cross-project alignment scoring."""

import logging
from uuid import UUID

from app.db.base import DatabaseProvider
from app.models.pydantic.models import (
    EntityStatus,
    ScorecardEntityRow,
    ScorecardEntityStatus,
    ScorecardProject,
    ScorecardResponse,
)

logger = logging.getLogger(__name__)

_DEFAULT_STATUS_LABELS: dict[str, str] = {
    "solid_approval": "Solid Approval",
    "leaning_approval": "Leaning Approval",
    "neutral": "Neutral",
    "leaning_disapproval": "Leaning Disapproval",
    "solid_disapproval": "Solid Disapproval",
    "unknown": "Unknown",
}


def _resolve_label(status: EntityStatus, status_labels: dict[str, str] | None) -> str:
    """Resolve the display label for a status using project config or defaults."""
    if status_labels and status.value in status_labels:
        return status_labels[status.value]
    return _DEFAULT_STATUS_LABELS.get(status.value, "Unknown")


class ScorecardService:
    """Assembles cross-project scorecard data with alignment scoring."""

    def __init__(
        self,
        projects_provider: DatabaseProvider,
        entities_provider: DatabaseProvider,
        status_records_provider: DatabaseProvider,
        districts_provider: DatabaseProvider,
    ):
        self.projects_provider = projects_provider
        self.entities_provider = entities_provider
        self.status_records_provider = status_records_provider
        self.districts_provider = districts_provider

    async def get_scorecard(self, group_id: UUID, group_name: str) -> ScorecardResponse:
        """Build a full scorecard for all active projects in a group.

        Fetches projects, entities, and status records in three queries (no N+1).
        Entities missing a status record are treated as UNKNOWN.
        """
        # 1. Fetch all active projects for the group
        projects = await self.projects_provider.filter_multiple(
            filters={"group_id": group_id, "status": "active"},
            in_filters=None,
        )
        if not projects:
            return ScorecardResponse(
                group_name=group_name,
                representative_title="Representative",
                projects=[],
                entities=[],
            )

        # Build ScorecardProject list
        scorecard_projects = [
            ScorecardProject(
                id=p.id,
                title=p.title,
                slug=p.slug,
                description=p.description,
                preferred_status=p.preferred_status,
                status_labels=(
                    p.dashboard_config.status_labels
                    if p.dashboard_config and p.dashboard_config.status_labels
                    else None
                ),
            )
            for p in projects
        ]

        # Derive representative_title from the first project's dashboard_config
        representative_title = "Representative"
        first_project = projects[0]
        if (
            first_project.dashboard_config
            and first_project.dashboard_config.representative_title
        ):
            representative_title = first_project.dashboard_config.representative_title

        # 2. Get jurisdiction from the first project (all scorecard projects share one jurisdiction)
        jurisdiction_id = first_project.jurisdiction_id

        # 3. Fetch all entities for that jurisdiction
        entities = await self.entities_provider.filter(jurisdiction_id=jurisdiction_id)
        if not entities:
            return ScorecardResponse(
                group_name=group_name,
                representative_title=representative_title,
                projects=scorecard_projects,
                entities=[],
            )

        # Enrich entities with district names
        entities = await self._enrich_with_district_names(entities)

        # 4. Fetch all status records for these projects in one query, filter entities in Python
        project_ids = [p.id for p in projects]
        all_status_records = await self.status_records_provider.filter_multiple(
            filters={},
            in_filters={"project_id": project_ids},
        )

        # Build lookup: (entity_id, project_id) -> status
        entity_ids = {e.id for e in entities}
        status_lookup: dict[tuple[UUID, UUID], EntityStatus] = {}
        for record in all_status_records:
            if record.entity_id in entity_ids:
                status_lookup[(record.entity_id, record.project_id)] = record.status

        # 5. Build entity rows
        entity_rows: list[ScorecardEntityRow] = []
        for entity in entities:
            statuses: dict[str, ScorecardEntityStatus] = {}
            aligned_count = 0
            total_scoreable = 0

            for sp in scorecard_projects:
                status = status_lookup.get((entity.id, sp.id), EntityStatus.UNKNOWN)
                label = _resolve_label(status, sp.status_labels)
                statuses[str(sp.id)] = ScorecardEntityStatus(status=status, label=label)

                # Only count projects where the entity was in office (not UNKNOWN).
                # An alder not serving at the time shouldn't affect their score.
                if status != EntityStatus.UNKNOWN:
                    total_scoreable += 1
                    if status == sp.preferred_status:
                        aligned_count += 1

            entity_rows.append(
                ScorecardEntityRow(
                    entity=entity,
                    statuses=statuses,
                    aligned_count=aligned_count,
                    total_scoreable=total_scoreable,
                )
            )

        return ScorecardResponse(
            group_name=group_name,
            representative_title=representative_title,
            projects=scorecard_projects,
            entities=entity_rows,
        )

    async def _enrich_with_district_names(self, entities: list) -> list:
        """Batch-fetch district names and attach them to entities."""
        district_ids = [e.district_id for e in entities if e.district_id]
        if not district_ids:
            return entities
        districts = await self.districts_provider.filter_in("id", district_ids)
        district_map = {d.id: d.name for d in districts}
        for entity in entities:
            if entity.district_id and entity.district_id in district_map:
                entity.district_name = district_map[entity.district_id]
        return entities
