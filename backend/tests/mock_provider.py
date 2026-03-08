"""In-memory database provider for testing."""

from copy import deepcopy
from typing import Any, List
from uuid import UUID, uuid4

from app.db.base import DatabaseProvider


class MockDatabaseProvider(DatabaseProvider):
    """In-memory database provider for testing."""

    def __init__(self):
        self._store: dict[UUID, Any] = {}

    async def get(self, id: UUID) -> Any | None:
        return deepcopy(self._store.get(id))

    async def list(self, skip: int = 0, limit: int = 100) -> List[Any]:
        items = list(self._store.values())
        return deepcopy(items[skip : skip + limit])

    async def create(self, obj_in: Any) -> Any:
        if isinstance(obj_in, dict):
            obj = deepcopy(obj_in)
            obj_id = obj.get("id", uuid4())
            self._store[obj_id] = obj
            return deepcopy(obj)
        obj = deepcopy(obj_in)
        if hasattr(obj, "id"):
            self._store[obj.id] = obj
        return deepcopy(obj)

    async def update(self, id: UUID, obj_in: Any) -> Any | None:
        if id not in self._store:
            return None
        existing = self._store[id]
        if isinstance(obj_in, dict):
            if hasattr(existing, "model_copy"):
                self._store[id] = existing.model_copy(update=obj_in)
            else:
                existing.update(obj_in)
                self._store[id] = existing
        else:
            self._store[id] = deepcopy(obj_in)
        return deepcopy(self._store[id])

    async def delete(self, id: UUID) -> bool:
        if id in self._store:
            del self._store[id]
            return True
        return False

    async def filter(self, **filters) -> List[Any]:
        results = []
        for item in self._store.values():
            match = True
            for field, value in filters.items():
                item_val = (
                    getattr(item, field, None)
                    if hasattr(item, field)
                    else (item.get(field) if isinstance(item, dict) else None)
                )
                if item_val != value:
                    match = False
                    break
            if match:
                results.append(deepcopy(item))
        return results

    async def filter_in(self, field: str, values: List[Any]) -> List[Any]:
        results = []
        for item in self._store.values():
            item_val = (
                getattr(item, field, None)
                if hasattr(item, field)
                else (item.get(field) if isinstance(item, dict) else None)
            )
            if item_val in values:
                results.append(deepcopy(item))
        return results

    async def filter_multiple(
        self, filters: dict[str, Any], in_filters: dict[str, List[Any]] | None = None
    ) -> List[Any]:
        results = []
        for item in self._store.values():
            match = True
            for field, value in filters.items():
                item_val = (
                    getattr(item, field, None)
                    if hasattr(item, field)
                    else (item.get(field) if isinstance(item, dict) else None)
                )
                if item_val != value:
                    match = False
                    break
            if match and in_filters:
                for field, values in in_filters.items():
                    item_val = (
                        getattr(item, field, None)
                        if hasattr(item, field)
                        else (item.get(field) if isinstance(item, dict) else None)
                    )
                    if item_val not in values:
                        match = False
                        break
            if match:
                results.append(deepcopy(item))
        return results

    def seed(self, obj: Any) -> None:
        """Directly seed an object into the store."""
        if hasattr(obj, "id"):
            self._store[obj.id] = deepcopy(obj)
        elif isinstance(obj, dict) and "id" in obj:
            self._store[obj["id"]] = deepcopy(obj)
