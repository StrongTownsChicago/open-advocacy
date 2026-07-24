from typing import Any
from uuid import UUID

from app.models.pydantic.models import EntityStatusRecord
from app.db.base import DatabaseProvider
from app.exceptions import NotFoundError


def _merge_preserved_fields(
    incoming: EntityStatusRecord, existing: EntityStatusRecord
) -> EntityStatusRecord:
    """Carry curated fields forward when the incoming record omits them.

    The upsert in :meth:`StatusService.create_status_record` replaces the whole
    record, so automated writers (scorecard refresh, import re-runs) that build
    records without ``record_metadata``/``notes`` would otherwise erase curated
    values. Semantics: ``None`` means "no opinion, keep what's stored"; an
    explicit empty value (``{}`` / ``""``) is an intentional clear.
    """
    preserved: dict[str, Any] = {}
    if incoming.record_metadata is None and existing.record_metadata is not None:
        preserved["record_metadata"] = existing.record_metadata
    if incoming.notes is None and existing.notes is not None:
        preserved["notes"] = existing.notes
    if not preserved:
        return incoming
    return incoming.model_copy(update=preserved)


class StatusService:
    def __init__(
        self,
        status_records_provider: DatabaseProvider,
        projects_provider: DatabaseProvider,
        entities_provider: DatabaseProvider,
    ):
        self.status_records_provider = status_records_provider
        self.projects_provider = projects_provider
        self.entities_provider = entities_provider

    async def list_status_records(
        self, project_id: UUID | None = None, entity_id: UUID | None = None
    ) -> list[EntityStatusRecord]:
        """List status records with optional filtering."""
        filters: dict[str, object] = {}
        in_filters: dict[str, list[object]] = {}

        if project_id:
            filters["project_id"] = project_id

        if entity_id:
            filters["entity_id"] = entity_id

        if filters or in_filters:
            status_records = await self.status_records_provider.filter_multiple(
                filters, in_filters
            )
        else:
            status_records = await self.status_records_provider.list()

        return status_records

    async def get_status_record(self, record_id: UUID) -> EntityStatusRecord | None:
        """Get a status record by ID."""
        return await self.status_records_provider.get(record_id)

    async def create_status_record(
        self, status_record: EntityStatusRecord
    ) -> EntityStatusRecord:
        """Create a new status record or update an existing one."""
        # Verify project exists
        project = await self.projects_provider.get(status_record.project_id)
        if not project:
            raise NotFoundError("Project not found")

        # Verify entity exists
        entity = await self.entities_provider.get(status_record.entity_id)
        if not entity:
            raise NotFoundError("Entity not found")

        # Check if status record already exists for this entity and project
        existing_records = await self.status_records_provider.filter_multiple(
            filters={
                "entity_id": status_record.entity_id,
                "project_id": status_record.project_id,
            },
            in_filters=None,
        )
        if existing_records:
            record = existing_records[0]
            payload = _merge_preserved_fields(status_record, record)
            updated = await self.status_records_provider.update(record.id, payload)
            if updated is None:
                raise ValueError("Failed to update existing status record")
            return updated

        return await self.status_records_provider.create(status_record)

    async def update_status_record(
        self, record_id: UUID, status_record: EntityStatusRecord
    ) -> EntityStatusRecord | None:
        """Update an existing status record."""
        existing_record = await self.status_records_provider.get(record_id)
        if not existing_record:
            return None

        return await self.status_records_provider.update(record_id, status_record)

    async def delete_status_record(self, record_id: UUID) -> bool:
        """Delete a status record by ID."""
        existing_record = await self.status_records_provider.get(record_id)
        if not existing_record:
            return False

        return await self.status_records_provider.delete(record_id)
