from uuid import UUID

from app.models.pydantic.models import EntityStatusRecord
from app.db.base import DatabaseProvider


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
            raise ValueError("Project not found")

        # Verify entity exists
        entity = await self.entities_provider.get(status_record.entity_id)
        if not entity:
            raise ValueError("Entity not found")

        # Check if status record already exists for this entity and project
        existing_records = await self.status_records_provider.list()
        for record in existing_records:
            if (
                record.entity_id == status_record.entity_id
                and record.project_id == status_record.project_id
            ):
                # Update existing record
                updated_record = await self.status_records_provider.update(
                    record.id, status_record
                )
                if updated_record is None:
                    raise ValueError("Failed to update existing status record")
                return updated_record

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
