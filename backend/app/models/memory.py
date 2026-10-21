"""Memory unit database model."""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Integer,
    Index,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class MemoryUnit(Base):
    """A single extracted memory unit (fact, observation, or insight)."""
    
    __tablename__ = "memory_units"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Metadata
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    memory_metadata: Mapped[dict] = mapped_column("memory_metadata", JSON, default=dict, nullable=False)
    observation_scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    
    # Consolidation status
    is_consolidated: Mapped[bool] = mapped_column(default=False, nullable=False)
    consolidated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consolidation_batch_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    observations: Mapped[list["MemoryObservation"]] = relationship(
        back_populates="source_unit",
        foreign_keys="MemoryObservation.source_memory_id",
        cascade="all, delete-orphan",
    )
    
    __table_args__ = (
        Index("ix_memory_units_document_consolidated", "document_id", "is_consolidated"),
        UniqueConstraint("document_id", "content_hash", name="uq_document_content_hash"),
    )

    @property
    def metadata_dict(self) -> dict:
        """Return metadata for serialization."""
        return self.memory_metadata

class MemoryObservation(Base):
    """An observation linking memory units (e.g., derived facts, relationships)."""
    
    __tablename__ = "memory_observations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_memory_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("memory_units.id", ondelete="CASCADE"), nullable=False
    )
    target_memory_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("memory_units.id", ondelete="CASCADE"), nullable=False
    )
    observation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(default=1.0, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    source_unit: Mapped["MemoryUnit"] = relationship(
        back_populates="observations", foreign_keys=[source_memory_id]
    )
    target_unit: Mapped["MemoryUnit"] = relationship(foreign_keys=[target_memory_id])
    
    __table_args__ = (
        Index("ix_observations_source", "source_memory_id"),
        Index("ix_observations_target", "target_memory_id"),
        UniqueConstraint(
            "source_memory_id", "target_memory_id", "observation_type",
            name="uq_observation_unique"
        ),
    )


class ConsolidationBatch(Base):
    """Record of a consolidation job execution."""
    
    __tablename__ = "consolidation_batches"
    
    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # pending, running, completed, failed
    units_processed: Mapped[int] = mapped_column(default=0, nullable=False)
    units_created: Mapped[int] = mapped_column(default=0, nullable=False)
    units_merged: Mapped[int] = mapped_column(default=0, nullable=False)
    units_deleted: Mapped[int] = mapped_column(default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("ix_consolidation_batches_document_status", "document_id", "status"),
    )


class AuditLog(Base):
    """Audit log for all mutating operations."""
    
    __tablename__ = "audit_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)  # user id or "system"
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # create, update, delete, consolidate
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)  # memory_unit, observation, batch
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    before: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    __table_args__ = (
        Index("ix_audit_log_resource", "resource_type", "resource_id"),
        Index("ix_audit_log_actor_created", "actor", "created_at"),
    )