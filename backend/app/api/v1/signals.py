"""Signal-related API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Signal, SignalType, Severity
from app.schemas.common import APIResponse
from app.schemas.signal import (
    SignalResponse,
    SignalListResponse,
    SignalMarkReadRequest,
    UnreadCountResponse,
)
from app.schemas.price import ProviderResponse, SKUResponse

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("")
async def get_signals(
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    severity: Optional[str] = Query(None, description="Filter by severity: high, medium, low"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SignalListResponse]:
    """Get list of signals with filtering."""
    
    # Build query
    query = (
        select(Signal)
        .options(selectinload(Signal.provider), selectinload(Signal.sku))
        .order_by(Signal.triggered_at.desc())
    )
    
    # Apply filters
    if signal_type:
        query = query.where(Signal.signal_type == signal_type)
    if severity:
        query = query.where(Signal.severity == severity)
    if is_read is not None:
        query = query.where(Signal.is_read == is_read)
    if start_date:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        query = query.where(Signal.triggered_at >= start_dt)
    if end_date:
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query = query.where(Signal.triggered_at <= end_dt)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get unread count
    unread_query = select(func.count()).where(Signal.is_read == False)
    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar()
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    signals = []
    for r in records:
        provider_resp = None
        if r.provider:
            provider_resp = ProviderResponse(
                id=r.provider.id,
                code=r.provider.code,
                name=r.provider.name,
                sector=r.provider.sector.value
            )
        
        sku_resp = None
        if r.sku:
            sku_resp = SKUResponse(
                id=r.sku.id,
                provider_id=r.sku.provider_id,
                code=r.sku.code,
                name=r.sku.name,
                category=r.sku.category
            )
        
        signals.append(SignalResponse(
            id=r.id,
            triggered_at=r.triggered_at,
            signal_type=r.signal_type.value,
            metric_id=r.metric_id,
            direction=r.direction,
            magnitude=r.magnitude,
            description=r.description,
            severity=r.severity.value,
            provider=provider_resp,
            sku=sku_resp,
            previous_value=float(r.previous_value) if r.previous_value else None,
            current_value=float(r.current_value) if r.current_value else None,
            source_url=r.source_url,
            stage_implication=r.stage_implication,
            is_read=r.is_read,
            created_at=r.created_at
        ))
    
    return APIResponse(
        data=SignalListResponse(
            signals=signals,
            total=total,
            unread_count=unread_count
        ),
        meta={
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(signals) < total
        }
    )


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UnreadCountResponse]:
    """Get count of unread signals."""
    
    query = select(func.count()).where(Signal.is_read == False)
    result = await db.execute(query)
    count = result.scalar()
    
    return APIResponse(data=UnreadCountResponse(count=count))


@router.get("/{signal_id}")
async def get_signal(
    signal_id: int,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SignalResponse]:
    """Get a specific signal by ID."""
    
    query = (
        select(Signal)
        .options(selectinload(Signal.provider), selectinload(Signal.sku))
        .where(Signal.id == signal_id)
    )
    
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    provider_resp = None
    if record.provider:
        provider_resp = ProviderResponse(
            id=record.provider.id,
            code=record.provider.code,
            name=record.provider.name,
            sector=record.provider.sector.value
        )
    
    sku_resp = None
    if record.sku:
        sku_resp = SKUResponse(
            id=record.sku.id,
            provider_id=record.sku.provider_id,
            code=record.sku.code,
            name=record.sku.name,
            category=record.sku.category
        )
    
    return APIResponse(
        data=SignalResponse(
            id=record.id,
            triggered_at=record.triggered_at,
            signal_type=record.signal_type.value,
            metric_id=record.metric_id,
            direction=record.direction,
            magnitude=record.magnitude,
            description=record.description,
            severity=record.severity.value,
            provider=provider_resp,
            sku=sku_resp,
            previous_value=float(record.previous_value) if record.previous_value else None,
            current_value=float(record.current_value) if record.current_value else None,
            source_url=record.source_url,
            stage_implication=record.stage_implication,
            is_read=record.is_read,
            created_at=record.created_at
        )
    )


@router.patch("/{signal_id}/read")
async def mark_signal_read(
    signal_id: int,
    request: SignalMarkReadRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """Mark a signal as read or unread."""
    
    # Check if signal exists
    query = select(Signal).where(Signal.id == signal_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Update
    stmt = update(Signal).where(Signal.id == signal_id).values(is_read=request.is_read)
    await db.execute(stmt)
    await db.commit()
    
    return APIResponse(
        data={"id": signal_id, "is_read": request.is_read}
    )
