"""Price-related API endpoints."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Provider, SKU, PriceRecord, SupplyChainPrice, SectorType
from app.schemas.common import APIResponse
from app.schemas.price import (
    LatestPriceResponse,
    PriceChange,
    PriceHistoryResponse,
    PriceHistoryPoint,
    PriceHistorySummary,
    DerivedIndexResponse,
    SupplyChainLatestResponse,
    SupplyChainPriceResponse,
    ProviderResponse,
    SKUResponse,
)

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/latest")
async def get_latest_prices(
    sector: Optional[str] = Query(None, description="Filter by sector: B, C"),
    provider: Optional[str] = Query(None, description="Filter by provider code"),
    category: Optional[str] = Query(None, description="Filter by category: flagship, economy, gpu"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Get latest prices for all tracked products."""
    
    # Build subquery for latest price per provider/sku/price_type
    subquery = (
        select(
            PriceRecord.provider_id,
            PriceRecord.sku_id,
            PriceRecord.price_type,
            func.max(PriceRecord.recorded_at).label("max_recorded_at")
        )
        .group_by(
            PriceRecord.provider_id,
            PriceRecord.sku_id,
            PriceRecord.price_type
        )
        .subquery()
    )
    
    # Main query with filters
    query = (
        select(PriceRecord)
        .join(Provider, PriceRecord.provider_id == Provider.id)
        .join(SKU, PriceRecord.sku_id == SKU.id)
        .join(
            subquery,
            and_(
                PriceRecord.provider_id == subquery.c.provider_id,
                PriceRecord.sku_id == subquery.c.sku_id,
                PriceRecord.price_type == subquery.c.price_type,
                PriceRecord.recorded_at == subquery.c.max_recorded_at
            )
        )
        .options(selectinload(PriceRecord.provider), selectinload(PriceRecord.sku))
        .where(Provider.is_active == True, SKU.is_active == True)
    )
    
    # Apply filters
    if sector:
        query = query.where(Provider.sector == sector)
    if provider:
        query = query.where(Provider.code == provider)
    if category:
        query = query.where(SKU.category == category)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Calculate week-over-week changes
    prices = []
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    for record in records:
        # Get price from a week ago
        week_ago_query = (
            select(PriceRecord.price)
            .where(
                PriceRecord.provider_id == record.provider_id,
                PriceRecord.sku_id == record.sku_id,
                PriceRecord.price_type == record.price_type,
                PriceRecord.recorded_at <= week_ago
            )
            .order_by(PriceRecord.recorded_at.desc())
            .limit(1)
        )
        week_ago_result = await db.execute(week_ago_query)
        week_ago_price = week_ago_result.scalar()
        
        wow_change = None
        if week_ago_price and week_ago_price > 0:
            wow_change = round(float((record.price - week_ago_price) / week_ago_price * 100), 2)
        
        prices.append(LatestPriceResponse(
            id=record.id,
            recorded_at=record.recorded_at,
            provider=ProviderResponse(
                id=record.provider.id,
                code=record.provider.code,
                name=record.provider.name,
                sector=record.provider.sector.value
            ),
            sku=SKUResponse(
                id=record.sku.id,
                provider_id=record.sku.provider_id,
                code=record.sku.code,
                name=record.sku.name,
                category=record.sku.category
            ),
            price_type=record.price_type.value,
            price=record.price,
            currency=record.currency,
            unit=record.unit,
            source_url=record.source_url,
            changes=PriceChange(wow=wow_change)
        ))
    
    return APIResponse(
        data={
            "prices": [p.model_dump() for p in prices],
            "updated_at": datetime.utcnow().isoformat()
        },
        meta={
            "total": len(prices),
            "sectors": {
                "B": len([p for p in prices if p.provider.sector == "B"]),
                "C": len([p for p in prices if p.provider.sector == "C"]),
            }
        }
    )


@router.get("/history")
async def get_price_history(
    provider: str = Query(..., description="Provider code"),
    sku: str = Query(..., description="SKU code"),
    price_type: Optional[str] = Query("input", description="Price type"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[PriceHistoryResponse]:
    """Get historical prices for a specific product."""
    
    # Parse dates
    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    else:
        start_dt = datetime.utcnow() - timedelta(days=365)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    else:
        end_dt = datetime.utcnow()
    
    # Query
    query = (
        select(PriceRecord)
        .join(Provider, PriceRecord.provider_id == Provider.id)
        .join(SKU, PriceRecord.sku_id == SKU.id)
        .where(
            Provider.code == provider,
            SKU.code == sku,
            PriceRecord.recorded_at >= start_dt,
            PriceRecord.recorded_at <= end_dt,
        )
        .order_by(PriceRecord.recorded_at.asc())
    )
    
    if price_type:
        query = query.where(PriceRecord.price_type == price_type)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    if not records:
        return APIResponse(
            data=PriceHistoryResponse(
                provider=provider,
                sku=sku,
                price_type=price_type,
                history=[],
                summary=PriceHistorySummary(
                    start_price=0,
                    end_price=0,
                    total_change_pct=0,
                    data_points=0
                )
            )
        )
    
    history = [
        PriceHistoryPoint(
            date=r.recorded_at.strftime("%Y-%m-%d"),
            price=float(r.price),
            source_url=r.source_url
        )
        for r in records
    ]
    
    start_price = float(records[0].price)
    end_price = float(records[-1].price)
    change_pct = ((end_price - start_price) / start_price * 100) if start_price > 0 else 0
    
    return APIResponse(
        data=PriceHistoryResponse(
            provider=provider,
            sku=sku,
            price_type=price_type,
            history=history,
            summary=PriceHistorySummary(
                start_price=start_price,
                end_price=end_price,
                total_change_pct=round(change_pct, 2),
                data_points=len(records)
            )
        )
    )


@router.get("/indices")
async def get_price_indices(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Get derived price indices."""
    
    # TODO: Calculate actual indices from data
    # For now, return mock data structure
    indices = [
        DerivedIndexResponse(
            metric_name="B_price_index",
            display_name="模型API价格指数",
            value=5.42,
            unit="USD/M tokens",
            calculated_at=datetime.utcnow(),
            changes=PriceChange(wow=-3.2, mom=-8.5, qoq=-15.2),
            description="旗舰模型加权平均价格"
        ),
        DerivedIndexResponse(
            metric_name="C_rental_index",
            display_name="GPU租赁价格指数",
            value=2.58,
            unit="USD/hour",
            calculated_at=datetime.utcnow(),
            changes=PriceChange(wow=0.8, mom=-2.1),
            description="H100独立云平均价格"
        ),
        DerivedIndexResponse(
            metric_name="B_china_discount",
            display_name="中国厂商折扣率",
            value=5.6,
            unit="percent",
            calculated_at=datetime.utcnow(),
            description="DeepSeek价格 / OpenAI价格"
        ),
        DerivedIndexResponse(
            metric_name="C_spot_discount",
            display_name="Spot折扣幅度",
            value=26.0,
            unit="percent",
            calculated_at=datetime.utcnow(),
            description="Spot价格 / On-demand价格"
        ),
    ]
    
    return APIResponse(
        data={"indices": [i.model_dump() for i in indices]}
    )
