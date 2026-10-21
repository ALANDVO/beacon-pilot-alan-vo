"""Memory unit API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.services.memory import MemoryService
from app.models.schemas import (
    MemoryUnitCreate,
    MemoryUnitUpdate,
    MemoryUnitResponse,
    MemoryUnitListResponse,
    PaginationParams,
    FilterParams,
    ConsolidationBatchCreate,
    ConsolidationBatchResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/memories", tags=["memories"])


async def get_memory_service() -> MemoryService:
    """Dependency to get memory service with DB session."""
    db = get_database()
    async with db.session() as session:
        yield MemoryService(session)


@router.post(
    "",
    response_model=MemoryUnitResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def create_memory(
    data: MemoryUnitCreate,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryUnitResponse:
    """Create a new memory unit."""
    try:
        return await service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "",
    response_model=MemoryUnitListResponse,
    responses={400: {"model": ErrorResponse}},
)
async def list_memories(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    is_consolidated: Optional[bool] = Query(None, description="Filter by consolidation status"),
    search: Optional[str] = Query(None, description="Search in content"),
    service: MemoryService = Depends(get_memory_service),
) -> MemoryUnitListResponse:
    """List memory units with pagination and filtering."""
    pagination = PaginationParams(page=page, page_size=page_size)
    filters = FilterParams(
        document_id=document_id,
        tag=tag,
        is_consolidated=is_consolidated,
        search=search,
    )
    return await service.list(pagination, filters)


@router.get(
    "/{unit_id}",
    response_model=MemoryUnitResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_memory(
    unit_id: int,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryUnitResponse:
    """Get a memory unit by ID."""
    unit = await service.get(unit_id)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory unit {unit_id} not found",
        )
    return unit


@router.patch(
    "/{unit_id}",
    response_model=MemoryUnitResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def update_memory(
    unit_id: int,
    data: MemoryUnitUpdate,
    service: MemoryService = Depends(get_memory_service),
) -> MemoryUnitResponse:
    """Update a memory unit."""
    unit = await service.update(unit_id, data)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory unit {unit_id} not found",
        )
    return unit


@router.delete(
    "/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_memory(
    unit_id: int,
    service: MemoryService = Depends(get_memory_service),
) -> None:
    """Delete a memory unit."""
    deleted = await service.delete(unit_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory unit {unit_id} not found",
        )