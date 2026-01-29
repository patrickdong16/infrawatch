"""Stage-related API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import StageSnapshot, DerivedMetric, StageCode, Confidence
from app.domain.stage_engine import StageEngine, StageMetrics
from app.schemas.common import APIResponse
from app.schemas.signal import (
    CurrentStageResponse,
    StageInfo,
    MetricStatus,
    TransitionRisk,
    StageHistoryResponse,
    StageHistoryPoint,
    M01Response,
    M01CompanyDetail,
)

router = APIRouter(prefix="/stage", tags=["stage"])


# Stage engine instance
stage_engine = StageEngine()


@router.get("/current")
async def get_current_stage(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[CurrentStageResponse]:
    """Get current infrastructure sustainability stage."""
    
    # Get latest metrics from database
    # TODO: Implement actual metric retrieval
    # For now, use sample data
    
    metrics = StageMetrics(
        m01_low=0.24,
        m01_high=0.36,
        b_qoq_deflation=0.08,
        c_spot_discount=0.26,
        c_rental_qoq=0.02,
        a_growth_streak=2,
        d3_margin_qoq=-0.02,
        e_supply_tightness=0.85,
    )
    
    # Determine stage
    result = stage_engine.determine(metrics)
    stage_info = stage_engine.get_stage_info(result.stage)
    
    # Build response
    key_metrics = {
        "M01": MetricStatus(
            value_low=metrics.m01_low,
            value_high=metrics.m01_high,
            status="transition" if 0.3 <= (metrics.m01_high or 0) <= 0.7 else "critical",
            trend="improving"
        ),
        "B_price_deflation_qoq": MetricStatus(
            value=metrics.b_qoq_deflation * 100 if metrics.b_qoq_deflation else None,
            status="moderate" if (metrics.b_qoq_deflation or 0) < 0.15 else "severe",
            trend="stable"
        ),
        "C_spot_discount": MetricStatus(
            value=metrics.c_spot_discount * 100 if metrics.c_spot_discount else None,
            status="balanced" if (metrics.c_spot_discount or 0) < 0.35 else "excess",
            trend="stable"
        ),
        "E_supply_tightness": MetricStatus(
            value=metrics.e_supply_tightness,
            status="tight" if (metrics.e_supply_tightness or 0) > 0.8 else "normal",
            trend="stable"
        ),
    }
    
    transition_risks = {}
    for key, risk_data in result.transition_risks.items():
        transition_risks[key] = TransitionRisk(
            probability=risk_data.get('probability', 'low'),
            conditions_met=risk_data.get('conditions_met', 0),
            conditions_total=risk_data.get('conditions_total', 0),
            details=risk_data.get('details'),
            gap=risk_data.get('gap')
        )
    
    return APIResponse(
        data=CurrentStageResponse(
            stage=StageInfo(
                code=result.stage.value,
                name=stage_info.get('name', ''),
                description=stage_info.get('description', '')
            ),
            confidence=result.confidence.value,
            rationale=result.rationale,
            determined_at=result.determined_at,
            key_metrics=key_metrics,
            transition_risks=transition_risks
        )
    )


@router.get("/history")
async def get_stage_history(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[StageHistoryResponse]:
    """Get stage determination history."""
    
    query = (
        select(StageSnapshot)
        .order_by(StageSnapshot.snapshot_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    history = [
        StageHistoryPoint(
            snapshot_at=r.snapshot_at,
            stage=r.stage.value,
            confidence=r.confidence.value,
            rationale=r.rationale
        )
        for r in records
    ]
    
    return APIResponse(
        data=StageHistoryResponse(
            history=history,
            total=len(history)
        )
    )


@router.get("/metrics")
async def get_stage_metrics(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Get all metrics used for stage determination."""
    
    # Get latest derived metrics
    query = (
        select(DerivedMetric)
        .order_by(DerivedMetric.calculated_at.desc())
        .limit(20)
    )
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Group by metric name
    metrics = {}
    for r in records:
        if r.metric_name not in metrics:
            metrics[r.metric_name] = {
                "value": float(r.value) if r.value else None,
                "value_low": float(r.value_low) if r.value_low else None,
                "value_high": float(r.value_high) if r.value_high else None,
                "company": r.company,
                "period": r.period,
                "calculated_at": r.calculated_at.isoformat()
            }
    
    return APIResponse(data={"metrics": metrics})


@router.get("/m01")
async def get_m01_analysis(
    period: Optional[str] = Query(None, description="Period (e.g., 2025-Q4)"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[M01Response]:
    """Get M01 coverage ratio analysis."""
    
    # TODO: Calculate from actual financial data
    # For now, return sample data
    
    companies = [
        M01CompanyDetail(
            company="MSFT",
            ai_revenue=13.0,
            total_capex=90.0,
            ai_capex_low=36.0,
            ai_capex_high=54.0,
            depreciation_years=4,
            m01_low=0.24,
            m01_high=0.36
        ),
        M01CompanyDetail(
            company="AMZN",
            ai_revenue=8.0,
            total_capex=75.0,
            ai_capex_low=30.0,
            ai_capex_high=45.0,
            depreciation_years=4,
            m01_low=0.18,
            m01_high=0.27
        ),
        M01CompanyDetail(
            company="GOOGL",
            ai_revenue=6.0,
            total_capex=93.0,
            ai_capex_low=37.2,
            ai_capex_high=55.8,
            depreciation_years=4,
            m01_low=0.11,
            m01_high=0.16
        ),
    ]
    
    # Calculate aggregate
    total_low = sum(c.m01_low for c in companies) / len(companies)
    total_high = sum(c.m01_high for c in companies) / len(companies)
    
    # Determine status
    if total_high < 0.3:
        status = "critical"
    elif total_low > 1.0:
        status = "sustainable"
    elif total_low > 0.7:
        status = "healthy"
    else:
        status = "transition"
    
    return APIResponse(
        data=M01Response(
            period=period or "2025-Q4",
            aggregate_low=round(total_low, 2),
            aggregate_high=round(total_high, 2),
            status=status,
            companies=companies,
            calculated_at=datetime.utcnow()
        )
    )
