"""Database models for price records and related entities."""

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


class SectorType(str, PyEnum):
    """Sector type enumeration."""
    B = "B"  # Model API pricing
    C = "C"  # GPU rental pricing
    A = "A"  # Enterprise adoption
    D = "D"  # Hyperscaler financials
    E = "E"  # Supply chain


class PriceType(str, PyEnum):
    """Price type enumeration."""
    INPUT = "input"
    OUTPUT = "output"
    HOURLY = "hourly"
    MONTHLY = "monthly"


class SupplyChainCategory(str, PyEnum):
    """Supply chain category enumeration."""
    HBM = "HBM"
    DRAM = "DRAM"
    GPU = "GPU"
    PACKAGING = "Packaging"


class Provider(Base):
    """Provider/vendor model."""
    
    __tablename__ = "providers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sector: Mapped[SectorType] = mapped_column(Enum(SectorType), nullable=False)
    website_url: Mapped[Optional[str]] = mapped_column(String(500))
    pricing_page_url: Mapped[Optional[str]] = mapped_column(String(500))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    skus: Mapped[list["SKU"]] = relationship("SKU", back_populates="provider")
    price_records: Mapped[list["PriceRecord"]] = relationship("PriceRecord", back_populates="provider")
    
    __table_args__ = (
        Index("idx_providers_sector", "sector"),
        Index("idx_providers_active", "is_active"),
    )


class SKU(Base):
    """SKU (Stock Keeping Unit) model - represents a specific product/model."""
    
    __tablename__ = "skus"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("providers.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))  # flagship, economy, gpu
    specs: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    provider: Mapped["Provider"] = relationship("Provider", back_populates="skus")
    price_records: Mapped[list["PriceRecord"]] = relationship("PriceRecord", back_populates="sku")
    
    __table_args__ = (
        Index("idx_skus_provider", "provider_id"),
        Index("idx_skus_category", "category"),
    )


class PriceRecord(Base):
    """Price record model - stores historical pricing data."""
    
    __tablename__ = "price_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("providers.id"), nullable=False)
    sku_id: Mapped[int] = mapped_column(Integer, ForeignKey("skus.id"), nullable=False)
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    commitment_type: Mapped[Optional[str]] = mapped_column(String(30))
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    provider: Mapped["Provider"] = relationship("Provider", back_populates="price_records")
    sku: Mapped["SKU"] = relationship("SKU", back_populates="price_records")
    
    __table_args__ = (
        Index("idx_price_records_provider_sku", "provider_id", "sku_id", "recorded_at"),
        Index("idx_price_records_type", "price_type", "recorded_at"),
    )


class SupplyChainPrice(Base):
    """Supply chain price record - E sector data."""
    
    __tablename__ = "supply_chain_prices"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category: Mapped[SupplyChainCategory] = mapped_column(Enum(SupplyChainCategory), nullable=False)
    item: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(30))
    mom_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    yoy_change: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    source: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_supply_chain_category", "category", "recorded_at"),
        Index("idx_supply_chain_item", "item", "recorded_at"),
    )
