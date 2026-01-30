"""Supply chain (E-sector) API endpoints."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml
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

# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent.parent.parent.parent / "config" / "supply_chain.yml"


def load_supply_chain_config() -> dict:
    """Load supply chain data from YAML config."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


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
    
    # Load derived indices from config
    config = load_supply_chain_config()
    derived_config = config.get("derived_indices", {})
    
    indices = {
        "E_hbm_premium": derived_config.get("E_hbm_premium", {}).get("value", 83.8),
        "E_memory_cost_index": derived_config.get("E_memory_cost_index", {}).get("value", 127.0),
        "E_supply_tightness": derived_config.get("E_supply_tightness", {}).get("value", 0.87),
        "E_gpu_margin_proxy": 2.5,  # 计算: GPU ASP 变化 - 内存成本变化
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
    
    # Load from config
    config = load_supply_chain_config()
    derived_config = config.get("derived_indices", {})
    
    # Helper to get config value with fallback
    def get_index(key: str, default_value: float, default_unit: str, default_desc: str, mom: float = 0, yoy: float = 0):
        cfg = derived_config.get(key, {})
        return DerivedIndexResponse(
            metric_name=key,
            display_name=cfg.get("description", default_desc).split("（")[0],  # 取描述前半部分作为显示名
            value=cfg.get("value", default_value),
            unit=cfg.get("unit", default_unit),
            calculated_at=datetime.utcnow(),
            changes=PriceChange(mom=mom, yoy=yoy) if mom or yoy else None,
            description=cfg.get("description", default_desc),
            trend_description=cfg.get("trend_description")  # 新增趋势描述字段
        )
    
    indices = [
        get_index("E_hbm_premium", 83.8, "倍", "HBM溢价倍数", mom=2.5, yoy=15.2),
        get_index("E_memory_cost_index", 147.6, "基准=100", "内存成本指数", mom=1.8, yoy=8.5),
        get_index("E_supply_tightness", 0.87, "0-1", "供应链紧张度", mom=0.02),
        DerivedIndexResponse(
            metric_name="E_cowos_utilization",
            display_name="CoWoS产能利用率",
            value=98.0,
            unit="percent",
            calculated_at=datetime.utcnow(),
            changes=PriceChange(mom=0.0, yoy=8.0),
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


@router.get("/config-history")
async def get_config_history(
    category: str = Query(..., description="Price category: hbm, dram, gpu, packaging"),
) -> APIResponse[dict]:
    """Get historical prices from YAML config file."""
    
    config = load_supply_chain_config()
    
    # Map category to config key
    category_map = {
        "hbm": "hbm",
        "dram": "dram", 
        "gpu": "gpu",
        "packaging": "packaging"
    }
    
    config_key = category_map.get(category.lower())
    if not config_key:
        return APIResponse(
            success=False,
            error=f"Unknown category: {category}"
        )
    
    items_data = config.get(config_key, [])
    
    # Get history for the first item (main item)
    history = []
    item_name = None
    unit = None
    trend_description = None
    
    if items_data and len(items_data) > 0:
        first_item = items_data[0]
        item_name = first_item.get("item")
        unit = first_item.get("unit", "USD")
        trend_description = first_item.get("trend_description")
        
        raw_history = first_item.get("history", [])
        for point in raw_history:
            history.append({
                "date": point.get("date"),
                "price": point.get("price"),
                "note": point.get("note", "")
            })
    
    return APIResponse(
        data={
            "category": category,
            "item": item_name,
            "unit": unit,
            "trend_description": trend_description,
            "history": history,
            "data_points": len(history)
        }
    )

