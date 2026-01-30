"""Pydantic schemas for price-related API endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProviderBase(BaseModel):
    """Base provider schema."""
    code: str
    name: str
    sector: str


class ProviderResponse(ProviderBase):
    """Provider response schema."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class SKUBase(BaseModel):
    """Base SKU schema."""
    code: str
    name: str
    category: Optional[str] = None


class SKUResponse(SKUBase):
    """SKU response schema."""
    id: int
    provider_id: int
    
    model_config = ConfigDict(from_attributes=True)


class PriceRecordBase(BaseModel):
    """Base price record schema."""
    recorded_at: datetime
    price_type: str
    price: Decimal
    currency: str = "USD"
    unit: Optional[str] = None
    source_url: Optional[str] = None


class PriceRecordResponse(PriceRecordBase):
    """Price record response schema."""
    id: int
    provider: ProviderResponse
    sku: SKUResponse
    
    model_config = ConfigDict(from_attributes=True)


class PriceChange(BaseModel):
    """Price change metrics."""
    wow: Optional[float] = None  # Week over week
    mom: Optional[float] = None  # Month over month
    qoq: Optional[float] = None  # Quarter over quarter


class LatestPriceResponse(BaseModel):
    """Latest price with change metrics."""
    id: int
    recorded_at: datetime
    provider: ProviderResponse
    sku: SKUResponse
    price_type: str
    price: Decimal
    currency: str
    unit: Optional[str]
    source_url: Optional[str]
    changes: PriceChange
    
    model_config = ConfigDict(from_attributes=True)


class PriceHistoryPoint(BaseModel):
    """Single point in price history."""
    date: str
    price: float
    source_url: Optional[str] = None


class PriceHistorySummary(BaseModel):
    """Price history summary statistics."""
    start_price: float
    end_price: float
    total_change_pct: float
    data_points: int


class PriceHistoryResponse(BaseModel):
    """Price history response."""
    provider: str
    sku: str
    price_type: Optional[str]
    history: list[PriceHistoryPoint]
    summary: PriceHistorySummary


class DerivedIndexResponse(BaseModel):
    """Derived index/metric response."""
    metric_name: str
    display_name: str
    value: Optional[float]
    value_low: Optional[float] = None
    value_high: Optional[float] = None
    unit: Optional[str]
    calculated_at: datetime
    changes: Optional[PriceChange] = None
    description: Optional[str] = None
    trend_description: Optional[str] = None  # 趋势描述，如"自2025年中开始持续上涨"
    
    model_config = ConfigDict(from_attributes=True)


class SupplyChainPriceBase(BaseModel):
    """Base supply chain price schema."""
    recorded_at: datetime
    category: str
    item: str
    price: Decimal
    unit: Optional[str] = None
    mom_change: Optional[float] = None
    yoy_change: Optional[float] = None
    source: Optional[str] = None


class SupplyChainPriceResponse(SupplyChainPriceBase):
    """Supply chain price response schema."""
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class SupplyChainLatestResponse(BaseModel):
    """Latest supply chain prices."""
    prices: list[SupplyChainPriceResponse]
    indices: dict[str, float]  # E_hbm_premium, E_supply_tightness, etc.
    updated_at: datetime
