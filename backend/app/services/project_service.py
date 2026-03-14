from uuid import UUID

from app.models.pydantic.models import (
    Project,
    ProjectBase,
    ProjectStatus,
    StatusDistribution,
    EntityStatus,
    EntityStatusRecord,
)
from app.db.base import DatabaseProvider
from app.exceptions import NotFoundError


class ProjectService:
    def __init__(
        self,
        projects_provider: DatabaseProvider,
        status_records_provider: DatabaseProvider,
        entities_provider: DatabaseProvider,
        jurisdictions_provider: DatabaseProvider,
        groups_provider: DatabaseProvider,
    ):
        self.projects_provider = projects_provider
        self.status_records_provider = status_records_provider
        self.entities_provider = entities_provider
        self.jurisdictions_provider = jurisdictions_provider
        self.groups_provider = groups_provider

    async def get_project(self, project_id: UUID) -> Project | None:
        """Get a project by ID."""
        return await self.projects_provider.get(project_id)

    async def get_project_with_details(self, project_id: UUID) -> Project | None:
        """Get a project by ID with enriched status and jurisdiction data."""
        project = await self.projects_provider.get(project_id)
        if not project:
            return None

        # Add jurisdiction name
        if project.jurisdiction_id:
            jurisdiction = await self.jurisdictions_provider.get(
                project.jurisdiction_id
            )
            if jurisdiction and jurisdiction.name:
                project.jurisdiction_name = jurisdiction.name

        # Add status distribution
        project.status_distribution = await self.get_project_status_distribution(
            project_id=project_id, project=project
        )

        return project

    async def get_project_by_name(self, name: str) -> Project | None:
        """Get a project by its title/name."""
        projects = await self.projects_provider.filter(title=name)
        if projects:
            return await self.get_project_with_details(projects[0].id)
        return None

    async def get_project_by_slug(self, slug: str) -> Project | None:
        """Get a project by its slug."""
        projects = await self.projects_provider.filter(slug=slug)
        if projects:
            return await self.get_project_with_details(projects[0].id)
        return None

    async def list_projects(
        self,
        skip: int = 0,
        limit: int = 100,
        status: ProjectStatus | None = None,
        group_id: UUID | None = None,
    ) -> list[Project]:
        """List projects with optional filtering and enriched data."""
        filters: dict[str, object] = {}
        in_filters: dict[str, list[object]] = {}

        if status:
            filters["status"] = status.value
        else:
            # Hide archived projects by default
            non_archived_statuses: list[object] = [
                s.value for s in ProjectStatus if s != ProjectStatus.ARCHIVED
            ]
            in_filters["status"] = non_archived_statuses

        if group_id:
            filters["group_id"] = group_id

        # Get projects with appropriate filters
        if filters or in_filters:
            projects = await self.projects_provider.filter_multiple(filters, in_filters)
        else:
            projects = await self.projects_provider.list(skip=skip, limit=limit)

        # Enrich projects with additional data
        if projects:
            projects = await self.enrich_projects_with_status_distributions(projects)
            projects = await self.enrich_projects_with_jurisdiction_name(projects)

        return projects

    async def create_project(self, project: ProjectBase) -> Project:
        """Create a new project after validating relations."""
        if project.group_id:
            group = await self.groups_provider.get(project.group_id)
            if not group:
                raise NotFoundError("Group not found")

        # Verify jurisdiction exists if provided
        if project.jurisdiction_id:
            jurisdiction = await self.jurisdictions_provider.get(
                project.jurisdiction_id
            )
            if not jurisdiction:
                raise NotFoundError("Jurisdiction not found")

        return await self.projects_provider.create(project)

    async def update_project(
        self, project_id: UUID, project: ProjectBase
    ) -> Project | None:
        """Update an existing project after validating relations."""
        existing_project = await self.projects_provider.get(project_id)
        if not existing_project:
            return None

        # Verify group exists if provided
        if project.group_id:
            group = await self.groups_provider.get(project.group_id)
            if not group:
                raise NotFoundError("Group not found")

        # Verify jurisdiction exists if provided
        if project.jurisdiction_id:
            jurisdiction = await self.jurisdictions_provider.get(
                project.jurisdiction_id
            )
            if not jurisdiction:
                raise NotFoundError("Jurisdiction not found")

        return await self.projects_provider.update(project_id, project)

    async def delete_project(self, project_id: UUID) -> bool:
        """Delete a project by ID."""
        existing_project = await self.projects_provider.get(project_id)
        if not existing_project:
            return False

        return await self.projects_provider.delete(project_id)

    async def get_project_status_distribution(
        self, project_id: UUID, project: Project | None = None
    ) -> StatusDistribution:
        """
        Get status distribution for a project, considering all entities in the project's jurisdiction.
        Entities without a status record are counted as unknown.

        Args:
            project_id: UUID of the project
            project: Optional Project object (to avoid fetching it again)

        Returns:
            StatusDistribution object
        """
        # Get project if not provided
        if not project:
            project = await self.projects_provider.get(project_id)
            if not project:
                return (
                    StatusDistribution()
                )  # Return empty distribution if project not found

        # Get ALL entities for the project's jurisdiction
        jurisdiction_id = project.jurisdiction_id
        jurisdiction_entities = await self.entities_provider.filter(
            jurisdiction_id=jurisdiction_id
        )

        if not jurisdiction_entities:
            return StatusDistribution()  # Return empty distribution if no entities

        # Total is the count of ALL entities in the jurisdiction
        total_entities = len(jurisdiction_entities)
        entity_ids = [entity.id for entity in jurisdiction_entities]

        # Get status records for the project and these entities
        try:
            project_status_records = await self.status_records_provider.filter_multiple(
                filters={"project_id": project_id}, in_filters={"entity_id": entity_ids}
            )
        except (AttributeError, NotImplementedError):
            # Fallback to the older approach if filter_multiple is not available
            all_status_records = await self.status_records_provider.list()
            project_status_records = [
                sr
                for sr in all_status_records
                if sr.project_id == project_id and sr.entity_id in entity_ids
            ]

        return self.calculate_status_distribution_with_unknowns(
            project_status_records, total_entities
        )

    async def enrich_projects_with_status_distributions(
        self, projects: list[Project]
    ) -> list[Project]:
        """
        Enrich a list of projects with their status distributions.

        Args:
            projects: List of Project objects

        Returns:
            List of Project objects with status_distribution field populated
        """
        if not projects:
            return []

        for project in projects:
            project.status_distribution = await self.get_project_status_distribution(
                project_id=project.id, project=project
            )

        return projects

    async def enrich_projects_with_jurisdiction_name(
        self, projects: list[Project]
    ) -> list[Project]:
        """
        Enrich a list of projects with their jurisdiction name.

        Args:
            projects: List of Project objects

        Returns:
            List of Project objects with jurisdiction_name field populated
        """
        if not projects:
            return []

        jurisdiction_ids = [p.jurisdiction_id for p in projects if p.jurisdiction_id]
        if not jurisdiction_ids:
            return projects

        jurisdictions = await self.jurisdictions_provider.filter_in(
            "id", jurisdiction_ids
        )
        jurisdiction_map = {j.id: j.name for j in jurisdictions if j.name}
        for project in projects:
            if project.jurisdiction_id and project.jurisdiction_id in jurisdiction_map:
                project.jurisdiction_name = jurisdiction_map[project.jurisdiction_id]

        return projects

    def calculate_status_distribution_with_unknowns(
        self, status_records: list[EntityStatusRecord], total_entity_count: int
    ) -> StatusDistribution:
        """
        Calculate the distribution of statuses for a list of entity status records,
        accounting for all entities in a jurisdiction (including those without explicit status).

        Args:
            status_records: List of status records for the project
            total_entity_count: Total number of entities in the jurisdiction

        Returns:
            StatusDistribution object
        """
        # Initialize all entities as unknown
        distribution = StatusDistribution(
            unknown=total_entity_count,  # Start with all entities as UNKNOWN
            total=total_entity_count,  # Total equals all entities in jurisdiction
        )

        # Create a mapping of entity_id to status for faster lookup
        entity_statuses = {record.entity_id: record.status for record in status_records}

        # Process explicit status records
        for _, status in entity_statuses.items():
            # Decrement the unknown count for non-unknown statuses
            distribution.unknown -= 1

            # Increment the appropriate status count
            if status == EntityStatus.SOLID_APPROVAL:
                distribution.solid_approval += 1
            elif status == EntityStatus.LEANING_APPROVAL:
                distribution.leaning_approval += 1
            elif status == EntityStatus.NEUTRAL:
                distribution.neutral += 1
            elif status == EntityStatus.LEANING_DISAPPROVAL:
                distribution.leaning_disapproval += 1
            elif status == EntityStatus.SOLID_DISAPPROVAL:
                distribution.solid_disapproval += 1
            else:
                distribution.unknown += 1

        return distribution
