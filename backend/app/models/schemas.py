"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Any


class MemoryUnitBase(BaseModel):
    """Base schema for memory unit."""
    document_id: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    metadata_dict: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    observation_scopes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class MemoryUnitCreate(MemoryUnitBase):
    """Schema for creating a memory unit."""
    pass


class MemoryUnitUpdate(BaseModel):
    """Schema for updating a memory unit."""
    content: Optional[str] = Field(None, min_length=1)
    tags: Optional[list[str]] = None
    metadata_dict: Optional[dict[str, Any]] = Field(None, alias="metadata")
    observation_scopes: Optional[list[str]] = None
    is_consolidated: Optional[bool] = None
    consolidated_at: Optional[datetime] = None
    consolidation_batch_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class MemoryUnitResponse(MemoryUnitBase):
    """Schema for memory unit response."""
    id: int
    content_hash: str
    is_consolidated: bool
    consolidated_at: Optional[datetime] = None
    consolidation_batch_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=False)


class MemoryUnitListResponse(BaseModel):
    """Paginated list of memory units."""
    items: list[MemoryUnitResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class MemoryObservationBase(BaseModel):
    """Base schema for memory observation."""
    source_memory_id: int
    target_memory_id: int
    observation_type: str = Field(..., min_length=1, max_length=64)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryObservationCreate(MemoryObservationBase):
    """Schema for creating a memory observation."""
    pass


class MemoryObservationResponse(MemoryObservationBase):
    """Schema for memory observation response."""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConsolidationBatchCreate(BaseModel):
    """Schema for creating a consolidation batch."""
    document_id: str = Field(..., min_length=1, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConsolidationBatchResponse(BaseModel):
    """Schema for consolidation batch response."""
    id: str
    document_id: str
    status: str
    units_processed: int
    units_created: int
    units_merged: int
    units_deleted: int
    error_message: Optional[str] = None
    metadata: dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConsolidationReport(BaseModel):
    """Report from a consolidation run."""
    batch_id: str
    document_id: str
    units_before: int
    units_after: int
    duplicates_found: int
    merged_pairs: list[tuple[int, int]]
    deleted_ids: list[int]
    new_units: list[MemoryUnitResponse]
    duration_ms: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    environment: str
    database: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    message: str
    details: Optional[dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    
    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: int) -> int:
        settings = None
        try:
            from app.core.config import get_settings
            settings = get_settings()
            return min(v, settings.max_page_size)
        except Exception:
            return min(v, 100)


class FilterParams(BaseModel):
    """Filter query parameters for memory units."""
    document_id: Optional[str] = None
    tag: Optional[str] = None
    is_consolidated: Optional[bool] = None
    search: Optional[str] = None