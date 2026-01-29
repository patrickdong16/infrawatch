"""Database models for signals, metrics, and stage snapshots."""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Index, Integer,
    Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SignalType(str, PyEnum):
    """Signal type enumeration."""
    PRICE_MOVE = "price_move"
    ADOPTION_INFLECTION = "adoption_inflection"
    COVERAGE_THRESHOLD = "coverage_threshold"
    SUPPLY_DEMAND_SHIFT = "supply_demand_shift"
    DISCLOSURE_CHANGE = "disclosure_change"
    SUPPLY_CHAIN_ALERT = "supply_chain_alert"


class Severity(str, PyEnum):
    """Signal severity level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StageCode(str, PyEnum):
    """Infrastructure sustainability stage."""
    S0 = "S0"  # Unsustainable
    S1 = "S1"  # Critical transition
    S2 = "S2"  # Early self-sustaining
    S3 = "S3"  # Mature industrialization


class Confidence(str, PyEnum):
    """Stage determination confidence level."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Signal(Base):
    """Signal log model - records significant metric changes."""
    
    __tablename__ = "signal_log"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    signal_type: Mapped[SignalType] = mapped_column(Enum(SignalType), nullable=False)
    metric_id: Mapped[Optional[str]] = mapped_column(String(10))
    provider_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("providers.id"))
    sku_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("skus.id"))
    direction: Mapped[Optional[str]] = mapped_column(String(4))  # up, down
    magnitude: Mapped[Optional[str]] = mapped_column(String(20))
    previous_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    current_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    stage_implication: Mapped[Optional[str]] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    provider: Mapped[Optional["Provider"]] = relationship("Provider")
    sku: Mapped[Optional["SKU"]] = relationship("SKU")
    
    __table_args__ = (
        Index("idx_signal_log_triggered", "triggered_at"),
        Index("idx_signal_log_type", "signal_type"),
        Index("idx_signal_log_severity", "severity"),
        Index("idx_signal_log_unread", "is_read"),
    )


# Import Provider and SKU for relationship typing
from app.models.price import Provider, SKU


class DerivedMetric(Base):
    """Derived metric model - calculated indicators."""
    
    __tablename__ = "derived_metrics"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    value_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    value_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6))
    company: Mapped[Optional[str]] = mapped_column(String(10))
    period: Mapped[Optional[str]] = mapped_column(String(10))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_derived_metrics_name_time", "metric_name", "calculated_at"),
        Index("idx_derived_metrics_company", "company", "metric_name"),
    )


class StageSnapshot(Base):
    """Stage snapshot model - records stage determinations over time."""
    
    __tablename__ = "stage_snapshots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    stage: Mapped[StageCode] = mapped_column(Enum(StageCode), nullable=False)
    confidence: Mapped[Confidence] = mapped_column(Enum(Confidence), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metrics_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_stage_snapshots_time", "snapshot_at"),
    )


class FinancialRecord(Base):
    """Financial record model - A and D sector quarterly data."""
    
    __tablename__ = "financial_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quarter: Mapped[str] = mapped_column(String(7), nullable=False)  # e.g., "2025-Q4"
    company: Mapped[str] = mapped_column(String(10), nullable=False)
    metric_id: Mapped[str] = mapped_column(String(10), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(30))
    yoy_change: Mapped[Optional[str]] = mapped_column(String(20))
    qoq_change: Mapped[Optional[str]] = mapped_column(String(20))
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_by: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    __table_args__ = (
        Index("idx_financial_company_quarter", "company", "quarter"),
        Index("idx_financial_metric", "metric_id"),
    )


class SpiderRun(Base):
    """Spider run log model - tracks crawler execution."""
    
    __tablename__ = "spider_runs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # running, success, failed
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_spider_runs_name_time", "spider_name", "started_at"),
        Index("idx_spider_runs_status", "status"),
    )
