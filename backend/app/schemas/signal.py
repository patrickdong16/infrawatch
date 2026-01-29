"""Pydantic schemas for signal and stage API endpoints."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.price import ProviderResponse, SKUResponse


class SignalBase(BaseModel):
    """Base signal schema."""
    triggered_at: datetime
    signal_type: str
    metric_id: Optional[str] = None
    direction: Optional[str] = None
    magnitude: Optional[str] = None
    description: str
    severity: str


class SignalResponse(SignalBase):
    """Signal response schema."""
    id: int
    provider: Optional[ProviderResponse] = None
    sku: Optional[SKUResponse] = None
    previous_value: Optional[float] = None
    current_value: Optional[float] = None
    source_url: Optional[str] = None
    stage_implication: Optional[str] = None
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SignalListResponse(BaseModel):
    """Signal list response with metadata."""
    signals: list[SignalResponse]
    total: int
    unread_count: int


class SignalMarkReadRequest(BaseModel):
    """Request to mark signal as read."""
    is_read: bool = True


class UnreadCountResponse(BaseModel):
    """Unread signal count response."""
    count: int


# Stage schemas

class StageInfo(BaseModel):
    """Stage information."""
    code: str
    name: str
    description: str


class MetricStatus(BaseModel):
    """Individual metric status for stage determination."""
    value: Optional[float] = None
    value_low: Optional[float] = None
    value_high: Optional[float] = None
    status: str  # good, warning, danger, neutral
    trend: Optional[str] = None  # improving, stable, declining


class TransitionRisk(BaseModel):
    """Risk assessment for stage transition."""
    probability: str  # high, medium, low
    conditions_met: int
    conditions_total: int
    details: Optional[dict] = None
    gap: Optional[dict] = None


class CurrentStageResponse(BaseModel):
    """Current stage response."""
    stage: StageInfo
    confidence: str
    rationale: str
    determined_at: datetime
    key_metrics: dict[str, MetricStatus]
    transition_risks: dict[str, TransitionRisk]


class StageHistoryPoint(BaseModel):
    """Single point in stage history."""
    snapshot_at: datetime
    stage: str
    confidence: str
    rationale: str


class StageHistoryResponse(BaseModel):
    """Stage history response."""
    history: list[StageHistoryPoint]
    total: int


# Financial record schemas

class FinancialRecordBase(BaseModel):
    """Base financial record schema."""
    quarter: str
    company: str
    metric_id: str
    value: Decimal
    unit: Optional[str] = None
    yoy_change: Optional[str] = None
    qoq_change: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None


class FinancialRecordCreate(FinancialRecordBase):
    """Create financial record schema."""
    pass


class FinancialRecordResponse(FinancialRecordBase):
    """Financial record response schema."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# M01 Coverage ratio schemas

class M01CompanyDetail(BaseModel):
    """M01 calculation detail for a company."""
    company: str
    ai_revenue: float
    total_capex: float
    ai_capex_low: float
    ai_capex_high: float
    depreciation_years: int
    m01_low: float
    m01_high: float


class M01Response(BaseModel):
    """M01 coverage ratio response."""
    period: str
    aggregate_low: float
    aggregate_high: float
    status: str  # critical, transition, healthy, sustainable
    companies: list[M01CompanyDetail]
    calculated_at: datetime
