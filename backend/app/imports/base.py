from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic

T = TypeVar("T")


class DataSource(ABC, Generic[T]):
    """Abstract base class for data sources."""

    @abstractmethod
    async def fetch_data(self) -> T:
        """Fetch data from the source."""
        pass

    @abstractmethod
    def get_source_info(self) -> dict[str, Any]:
        """Get information about the data source."""
        pass


class DataImporter(ABC):
    """Abstract base class for data importers."""

    @abstractmethod
    async def import_data(self, **kwargs: Any) -> dict[str, Any]:
        """Import data from a source into the system."""
        pass

    @abstractmethod
    async def validate_import(self, **kwargs: Any) -> bool:
        """Validate the data before import."""
        pass
