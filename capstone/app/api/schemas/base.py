from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StandardResponse(BaseModel):
    """Standard response envelope for single resource."""
    data: dict | list | None = None
    meta: dict | None = None


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    page_size: int
    total: int
    has_next: bool
