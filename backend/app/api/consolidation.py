"""Consolidation API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.services.memory import MemoryService
from app.models.schemas import (
    ConsolidationBatchCreate,
    ConsolidationBatchResponse,
    ConsolidationReport,
    ErrorResponse,
)

router = APIRouter(prefix="/consolidate", tags=["consolidation"])


async def get_memory_service() -> MemoryService:
    """Dependency to get memory service with DB session."""
    db = get_database()
    async with db.session() as session:
        yield MemoryService(session)


@router.post(
    "",
    response_model=ConsolidationBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def create_consolidation_batch(
    data: ConsolidationBatchCreate,
    service: MemoryService = Depends(get_memory_service),
) -> ConsolidationBatchResponse:
    """Create a new consolidation batch (async job)."""
    # Verify document exists
    from app.models.memory import MemoryUnit
    from sqlalchemy import select, func
    
    db = get_database()
    async with db.session() as check_session:
        result = await check_session.execute(
            select(func.count(MemoryUnit.id)).where(MemoryUnit.document_id == data.document_id)
        )
        count = result.scalar_one()
        if count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No memory units found for document {data.document_id}",
            )
    
    return await service.create_batch(data)


@router.get(
    "/{batch_id}",
    response_model=ConsolidationBatchResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_consolidation_batch(
    batch_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> ConsolidationBatchResponse:
    """Get consolidation batch status."""
    batch = await service.get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consolidation batch {batch_id} not found",
        )
    return batch


@router.post(
    "/{batch_id}/run",
    response_model=ConsolidationReport,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def run_consolidation(
    batch_id: str,
    service: MemoryService = Depends(get_memory_service),
) -> ConsolidationReport:
    """Run consolidation for a batch (synchronous for now)."""
    from ....services.consolidation import ConsolidationService
    
    batch = await service.get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Consolidation batch {batch_id} not found",
        )
    
    if batch.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Consolidation already running",
        )
    if batch.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Consolidation already completed",
        )
    
    # Update status to running
    await service.update_batch_status(batch_id, "running")
    
    # Run consolidation
    db = get_database()
    async with db.session() as session:
        consolidation_service = ConsolidationService(session)
        report = await consolidation_service.consolidate_document(batch.document_id, batch_id)
    
    # Update batch with results
    await service.update_batch_status(
        batch_id,
        "completed",
        units_processed=report.units_before,
        units_created=len(report.new_units),
        units_merged=len(report.merged_pairs),
        units_deleted=len(report.deleted_ids),
    )
    
    return report