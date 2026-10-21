"""Consolidation service for deduplicating and merging memory units."""
from datetime import datetime, timezone
from typing import Optional
from difflib import SequenceMatcher
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import MemoryUnit, MemoryObservation, ConsolidationBatch
from app.models.schemas import ConsolidationReport, MemoryUnitResponse


class ConsolidationService:
    """Service for memory consolidation operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.similarity_threshold = 0.85
    
    def _similarity(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def _find_duplicates(self, units: list[MemoryUnit]) -> list[tuple[int, int]]:
        """Find pairs of duplicate units based on content similarity."""
        duplicates = []
        for i, unit_a in enumerate(units):
            for unit_b in units[i + 1:]:
                if self._similarity(unit_a.content, unit_b.content) >= self.similarity_threshold:
                    duplicates.append((unit_a.id, unit_b.id))
        return duplicates
    
    async def _merge_units(self, primary_id: int, duplicate_id: int) -> MemoryUnit:
        """Merge duplicate unit into primary, combining metadata."""
        result = await self.session.execute(
            select(MemoryUnit).where(MemoryUnit.id.in_([primary_id, duplicate_id]))
        )
        units = {u.id: u for u in result.scalars().all()}
        
        primary = units[primary_id]
        duplicate = units[duplicate_id]
        
        # Merge tags (union)
        primary.tags = list(set(primary.tags + duplicate.tags))
        
        # Merge metadata (primary wins on conflict)
        merged_metadata = {**duplicate.metadata_, **primary.metadata_}
        primary.metadata_ = merged_metadata
        
        # Merge observation scopes (union)
        primary.observation_scopes = list(set(primary.observation_scopes + duplicate.observation_scopes))
        
        # Update observations pointing to duplicate to point to primary
        await self.session.execute(
            MemoryObservation.__table__.update()
            .where(MemoryObservation.target_memory_id == duplicate_id)
            .values(target_memory_id=primary_id)
        )
        
        # Delete duplicate
        await self.session.delete(duplicate)
        await self.session.flush()
        
        return primary
    
    async def consolidate_document(
        self,
        document_id: str,
        batch_id: str,
    ) -> ConsolidationReport:
        """Consolidate all memory units for a document."""
        import time
        start_time = time.perf_counter()
        
        # Get all units for document
        result = await self.session.execute(
            select(MemoryUnit).where(MemoryUnit.document_id == document_id)
        )
        units = list(result.scalars().all())
        
        units_before = len(units)
        if units_before == 0:
            return ConsolidationReport(
                batch_id=batch_id,
                document_id=document_id,
                units_before=0,
                units_after=0,
                duplicates_found=0,
                merged_pairs=[],
                deleted_ids=[],
                new_units=[],
                duration_ms=0,
            )
        
        # Find duplicates
        duplicate_pairs = self._find_duplicates(units)
        duplicates_found = len(duplicate_pairs)
        
        # Merge duplicates (keep first as primary)
        merged_pairs = []
        deleted_ids = []
        for primary_id, duplicate_id in duplicate_pairs:
            if duplicate_id not in deleted_ids:  # Skip if already merged
                await self._merge_units(primary_id, duplicate_id)
                merged_pairs.append((primary_id, duplicate_id))
                deleted_ids.append(duplicate_id)
        
        # Get final units
        result = await self.session.execute(
            select(MemoryUnit).where(MemoryUnit.document_id == document_id)
        )
        final_units = list(result.scalars().all())
        units_after = len(final_units)
        
        # Mark all as consolidated
        for unit in final_units:
            unit.is_consolidated = True
            unit.consolidated_at = datetime.now(timezone.utc)
            unit.consolidation_batch_id = batch_id
        
        await self.session.commit()
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        return ConsolidationReport(
            batch_id=batch_id,
            document_id=document_id,
            units_before=units_before,
            units_after=units_after,
            duplicates_found=duplicates_found,
            merged_pairs=merged_pairs,
            deleted_ids=deleted_ids,
            new_units=[MemoryUnitResponse.model_validate(u) for u in final_units],
            duration_ms=duration_ms,
        )