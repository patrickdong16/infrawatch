"""Supply chain (E-sector) API endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import SupplyChainPrice, SupplyChainCategory
from app.schemas.common import APIResponse
from app.schemas.price import (
    SupplyChainPriceResponse,
    SupplyChainLatestResponse,
    DerivedIndexResponse,
    PriceChange,
)

router = APIRouter(prefix="/supply-chain", tags=["supply-chain"])


@router.get("/latest")
async def get_latest_supply_chain_prices(
    category: Optional[str] = Query(None, description="Filter by category: HBM, DRAM, GPU, Packaging"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SupplyChainLatestResponse]:
    """Get latest supply chain prices."""
    
    # Build subquery for latest price per category/item
    subquery = (
        select(
            SupplyChainPrice.category,
            SupplyChainPrice.item,
            func.max(SupplyChainPrice.recorded_at).label("max_recorded_at")
        )
        .group_by(SupplyChainPrice.category, SupplyChainPrice.item)
        .subquery()
    )
    
    # Main query
    query = (
        select(SupplyChainPrice)
        .join(
            subquery,
            (SupplyChainPrice.category == subquery.c.category) &
            (SupplyChainPrice.item == subquery.c.item) &
            (SupplyChainPrice.recorded_at == subquery.c.max_recorded_at)
        )
    )
    
    if category:
        query = query.where(SupplyChainPrice.category == category)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    prices = [
        SupplyChainPriceResponse(
            id=r.id,
            recorded_at=r.recorded_at,
            category=r.category.value,
            item=r.item,
            price=r.price,
            unit=r.unit,
            mom_change=float(r.mom_change) if r.mom_change else None,
            yoy_change=float(r.yoy_change) if r.yoy_change else None,
            source=r.source
        )
        for r in records
    ]
    
    # Calculate derived indices
    # TODO: Calculate from actual data
    indices = {
        "E_hbm_premium": 83.8,  # HBM3e price / DDR5 price ratio
        "E_memory_cost_index": 127.0,  # Weighted memory cost index (base=100)
        "E_supply_tightness": 0.87,  # CoWoS utilization × HBM price trend
        "E_gpu_margin_proxy": 2.5,  # GPU ASP change - memory cost change
    }
    
    return APIResponse(
        data=SupplyChainLatestResponse(
            prices=prices,
            indices=indices,
            updated_at=datetime.utcnow()
        )
    )


@router.get("/history")
async def get_supply_chain_history(
    category: str = Query(..., description="Category: HBM, DRAM, GPU, Packaging"),
    item: str = Query(..., description="Item name"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Get historical supply chain prices."""
    
    # Parse dates
    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    else:
        start_dt = datetime.utcnow() - timedelta(days=365)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end_dt = datetime.utcnow()
    
    query = (
        select(SupplyChainPrice)
        .where(
            SupplyChainPrice.category == category,
            SupplyChainPrice.item == item,
            SupplyChainPrice.recorded_at >= start_dt,
            SupplyChainPrice.recorded_at <= end_dt,
        )
        .order_by(SupplyChainPrice.recorded_at.asc())
    )
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    history = [
        {
            "date": r.recorded_at.strftime("%Y-%m-%d"),
            "price": float(r.price),
            "unit": r.unit,
            "source": r.source
        }
        for r in records
    ]
    
    return APIResponse(
        data={
            "category": category,
            "item": item,
            "history": history,
            "data_points": len(history)
        }
    )


@router.get("/indices")
async def get_supply_chain_indices(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Get supply chain derived indices."""
    
    indices = [
        DerivedIndexResponse(
            metric_name="E_hbm_premium",
            display_name="HBM溢价倍数",
            value=83.8,
            unit="倍",
            calculated_at=datetime.utcnow(),
            changes=PriceChange(mom=2.5, yoy=15.2),
            description="HBM3e单位价格 / DDR5单位价格"
        ),
        DerivedIndexResponse(
            metric_name="E_memory_cost_index",
            display_name="内存成本指数",
            value=127.0,
            unit="基准=100",
            calculated_at=datetime.utcnow(),
            changes=PriceChange(mom=1.8, yoy=8.5),
            description="HBM + DRAM加权价格指数"
        ),
        DerivedIndexResponse(
            metric_name="E_supply_tightness",
            display_name="供应链紧张度",
            value=0.87,
            unit="0-1",
            calculated_at=datetime.utcnow(),
            changes=PriceChange(mom=0.02),
            description="CoWoS利用率 × HBM涨幅，>0.8为紧张"
        ),
        DerivedIndexResponse(
            metric_name="E_cowos_utilization",
            display_name="CoWoS产能利用率",
            value=98.0,
            unit="percent",
            calculated_at=datetime.utcnow(),
            description="台积电先进封装产能利用率"
        ),
    ]
    
    return APIResponse(
        data={"indices": [i.model_dump() for i in indices]}
    )


@router.get("/alerts")
async def get_supply_chain_alerts(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Get supply chain alert status."""
    
    # TODO: Calculate from actual data
    alerts = [
        {
            "type": "cost_increase_warning",
            "severity": "high",
            "message": "HBM价格连续3月上涨>5%，6-12月后基建成本上升预警",
            "trigger": "E1连续上涨 + E4>95%",
            "impact": "C板块价格上行压力，M01可能承压"
        },
        {
            "type": "supply_tight",
            "severity": "medium",
            "message": "CoWoS产能利用率持续满载（98%）",
            "trigger": "E4 > 95%",
            "impact": "GPU供应可能受限"
        }
    ]
    
    return APIResponse(
        data={
            "alerts": alerts,
            "supply_status": "tight",
            "overall_risk": "medium-high"
        }
    )
