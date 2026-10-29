"""Memory unit service layer."""
from datetime import datetime, timezone
from hashlib import sha256
from typing import Optional
import sys
from sqlalchemy import select, func, delete, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.memory import MemoryUnit, MemoryObservation, ConsolidationBatch, AuditLog
from app.models.schemas import (
    MemoryUnitCreate,
    MemoryUnitUpdate,
    MemoryUnitResponse,
    MemoryUnitListResponse,
    PaginationParams,
    FilterParams,
    ConsolidationBatchCreate,
    ConsolidationBatchResponse,
)
from app.core.config import get_settings


class MemoryService:
    """Service for memory unit operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
    
    def _hash_content(self, content: str) -> str:
        """Generate SHA256 hash of content."""
        return sha256(content.encode("utf-8")).hexdigest()
    
    async def create(self, data: MemoryUnitCreate, actor: str = "system") -> MemoryUnitResponse:
        """Create a new memory unit."""
        content_hash = self._hash_content(data.content)
        
        # Check for duplicate content hash within same document
        existing = await self.session.execute(
            select(MemoryUnit).where(
                and_(
                    MemoryUnit.document_id == data.document_id,
                    MemoryUnit.content_hash == content_hash,
                )
            )
        )
        existing_unit = existing.scalar_one_or_none()
        if existing_unit:
            print(f"[DEBUG] Duplicate found: document_id={data.document_id}, content_hash={content_hash}, existing_id={existing_unit.id}", file=sys.stderr)
            raise ValueError(f"Memory unit with same content already exists in document {data.document_id}")
        
        print(f"[DEBUG] Creating new unit: document_id={data.document_id}, content_hash={content_hash}", file=sys.stderr)
        unit = MemoryUnit(
            document_id=data.document_id,
            content=data.content,
            content_hash=content_hash,
            tags=data.tags,
            meta=data.metadata_dict,
            observation_scopes=data.observation_scopes,
        )
        self.session.add(unit)
        await self.session.flush()
        print(f"[DEBUG] After flush, unit.id={unit.id}", file=sys.stderr)
        
        # Audit log
        audit = AuditLog(
            actor=actor,
            action="create",
            resource_type="memory_unit",
            resource_id=str(unit.id),
            after={
                "document_id": unit.document_id,
                "content": unit.content,
                "tags": unit.tags,
                "metadata": unit.meta,
            },
        )
        self.session.add(audit)
        try:
            await self.session.commit()
            print(f"[DEBUG] Commit successful", file=sys.stderr)
        except Exception as e:
            print(f"[DEBUG] Commit failed: {e}", file=sys.stderr)
            await self.session.rollback()
            raise
        await self.session.refresh(unit)
        
        return MemoryUnitResponse.model_validate(unit)
    
    async def get(self, unit_id: int) -> Optional[MemoryUnitResponse]:
        """Get a memory unit by ID."""
        result = await self.session.execute(
            select(MemoryUnit).where(MemoryUnit.id == unit_id)
        )
        unit = result.scalar_one_or_none()
        if unit:
            return MemoryUnitResponse.model_validate(unit)
        return None
    
    async def list(
        self,
        pagination: PaginationParams,
        filters: FilterParams,
    ) -> MemoryUnitListResponse:
        """List memory units with pagination and filtering."""
        query = select(MemoryUnit)
        count_query = select(func.count(MemoryUnit.id))
        
        # Apply filters
        conditions = []
        if filters.document_id:
            conditions.append(MemoryUnit.document_id == filters.document_id)
        if filters.tag:
            # JSON array contains tag
            conditions.append(MemoryUnit.tags.contains([filters.tag]))
        if filters.is_consolidated is not None:
            conditions.append(MemoryUnit.is_consolidated == filters.is_consolidated)
        if filters.search:
            conditions.append(MemoryUnit.content.ilike(f"%{filters.search}%"))
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        query = query.order_by(MemoryUnit.created_at.desc())
        query = query.offset((pagination.page - 1) * pagination.page_size)
        query = query.limit(pagination.page_size)
        
        result = await self.session.execute(query)
        units = result.scalars().all()
        
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return MemoryUnitListResponse(
            items=[MemoryUnitResponse.model_validate(u) for u in units],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
        )
    
    async def update(
        self,
        unit_id: int,
        data: MemoryUnitUpdate,
        actor: str = "system",
    ) -> Optional[MemoryUnitResponse]:
        """Update a memory unit."""
        result = await self.session.execute(
            select(MemoryUnit).where(MemoryUnit.id == unit_id)
        )
        unit = result.scalar_one_or_none()
        if not unit:
            return None
        
        # Capture before state for audit
        before = {
            "document_id": unit.document_id,
            "content": unit.content,
            "tags": unit.tags,
            "metadata": unit.meta,
            "observation_scopes": unit.observation_scopes,
            "is_consolidated": unit.is_consolidated,
        }
        
        # Apply updates
        update_data = data.model_dump(exclude_unset=True)
        if "metadata" in update_data:
            update_data["meta"] = update_data.pop("metadata")
        
        for field, value in update_data.items():
            setattr(unit, field, value)
        
        
        unit.updated_at = datetime.now(timezone.utc)
        
        after = {
            "document_id": unit.document_id,
            "content": unit.content,
            "tags": unit.tags,
            "metadata": unit.meta,
            "observation_scopes": unit.observation_scopes,
            "is_consolidated": unit.is_consolidated,
        }
        audit = AuditLog(
            actor=actor,
            action="update",
            resource_type="memory_unit",
            resource_id=str(unit.id),
            before=before,
            after=after,
        )
        self.session.add(audit)
        
        await self.session.commit()
        await self.session.refresh(unit)
        
        return MemoryUnitResponse.model_validate(unit)
    
    async def delete(self, unit_id: int, actor: str = "system") -> bool:
        """Delete a memory unit."""
        result = await self.session.execute(
            select(MemoryUnit).where(MemoryUnit.id == unit_id)
        )
        unit = result.scalar_one_or_none()
        if not unit:
            return False
        
        # Audit log before deletion
        before = {
            "document_id": unit.document_id,
            "content": unit.content,
            "tags": unit.tags,
            "metadata": unit.metadata_,
        }
        audit = AuditLog(
            actor=actor,
            action="delete",
            resource_type="memory_unit",
            resource_id=str(unit.id),
            before=before,
        )
        self.session.add(audit)
        
        await self.session.delete(unit)
        await self.session.commit()
        return True
    
    async def create_batch(self, data: ConsolidationBatchCreate, actor: str = "system") -> ConsolidationBatchResponse:
        """Create a new consolidation batch record."""
        import uuid
        batch_id = str(uuid.uuid4())
        
        batch = ConsolidationBatch(
            id=batch_id,
            document_id=data.document_id,
            status="pending",
            metadata_=data.metadata,
        )
        self.session.add(batch)
        await self.session.commit()
        await self.session.refresh(batch)
        
        return ConsolidationBatchResponse.model_validate(batch)
    
    async def get_batch(self, batch_id: str) -> Optional[ConsolidationBatchResponse]:
        """Get a consolidation batch by ID."""
        result = await self.session.execute(
            select(ConsolidationBatch).where(ConsolidationBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if batch:
            return ConsolidationBatchResponse.model_validate(batch)
        return None
    
    async def update_batch_status(
        self,
        batch_id: str,
        status: str,
        units_processed: int = 0,
        units_created: int = 0,
        units_merged: int = 0,
        units_deleted: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[ConsolidationBatchResponse]:
        """Update consolidation batch status."""
        result = await self.session.execute(
            select(ConsolidationBatch).where(ConsolidationBatch.id == batch_id)
        )
        batch = result.scalar_one_or_none()
        if not batch:
            return None
        
        batch.status = status
        batch.units_processed = units_processed
        batch.units_created = units_created
        batch.units_merged = units_merged
        batch.units_deleted = units_deleted
        batch.error_message = error_message
        
        if status in ("completed", "failed"):
            batch.completed_at = datetime.now(timezone.utc)
        
        await self.session.commit()
        await self.session.refresh(batch)
        
        return ConsolidationBatchResponse.model_validate(batch)