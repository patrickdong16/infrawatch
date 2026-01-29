"""Database seed script - populates initial data."""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.database import async_session_maker, init_db
from app.models import (
    Provider, SKU, PriceRecord, SupplyChainPrice,
    Signal, DerivedMetric, StageSnapshot,
    SectorType, PriceType, SupplyChainCategory,
    SignalType, Severity, StageCode, Confidence
)


async def seed_providers():
    """Seed provider data."""
    providers = [
        # B Sector - Model API
        {"code": "openai", "name": "OpenAI", "sector": SectorType.B, "pricing_page_url": "https://platform.openai.com/docs/pricing"},
        {"code": "anthropic", "name": "Anthropic", "sector": SectorType.B, "pricing_page_url": "https://www.anthropic.com/pricing"},
        {"code": "google", "name": "Google", "sector": SectorType.B, "pricing_page_url": "https://ai.google.dev/pricing"},
        {"code": "deepseek", "name": "DeepSeek", "sector": SectorType.B, "pricing_page_url": "https://platform.deepseek.com/api-docs/pricing"},
        {"code": "together", "name": "Together AI", "sector": SectorType.B, "pricing_page_url": "https://www.together.ai/pricing"},
        # C Sector - GPU Rental
        {"code": "lambda", "name": "Lambda Labs", "sector": SectorType.C, "pricing_page_url": "https://lambdalabs.com/service/gpu-cloud"},
        {"code": "coreweave", "name": "CoreWeave", "sector": SectorType.C, "pricing_page_url": "https://www.coreweave.com/pricing"},
        {"code": "runpod", "name": "RunPod", "sector": SectorType.C, "pricing_page_url": "https://www.runpod.io/gpu-instance/pricing"},
        {"code": "vastai", "name": "Vast.ai", "sector": SectorType.C, "pricing_page_url": "https://vast.ai/"},
        # E Sector - Supply Chain
        {"code": "trendforce", "name": "TrendForce", "sector": SectorType.E, "pricing_page_url": "https://www.trendforce.com/"},
        {"code": "skhynix", "name": "SK海力士", "sector": SectorType.E, "pricing_page_url": "https://www.skhynix.com/ir/"},
    ]
    
    async with async_session_maker() as session:
        for p_data in providers:
            result = await session.execute(
                select(Provider).where(Provider.code == p_data["code"])
            )
            if not result.scalar_one_or_none():
                session.add(Provider(**p_data))
        await session.commit()
        print(f"Seeded {len(providers)} providers")


async def seed_skus():
    """Seed SKU data."""
    skus = [
        # OpenAI
        {"provider_code": "openai", "code": "gpt-4o", "name": "GPT-4o", "category": "flagship"},
        {"provider_code": "openai", "code": "gpt-4o-mini", "name": "GPT-4o Mini", "category": "economy"},
        # Anthropic
        {"provider_code": "anthropic", "code": "claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "category": "flagship"},
        {"provider_code": "anthropic", "code": "claude-3.5-haiku", "name": "Claude 3.5 Haiku", "category": "economy"},
        # Google
        {"provider_code": "google", "code": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "category": "flagship"},
        {"provider_code": "google", "code": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "category": "economy"},
        # DeepSeek
        {"provider_code": "deepseek", "code": "deepseek-v3", "name": "DeepSeek V3", "category": "flagship"},
        # GPU Rental
        {"provider_code": "lambda", "code": "h100-80gb", "name": "H100 80GB", "category": "gpu"},
        {"provider_code": "coreweave", "code": "h100-80gb", "name": "H100 80GB", "category": "gpu"},
        {"provider_code": "runpod", "code": "h100-80gb", "name": "H100 80GB", "category": "gpu"},
        {"provider_code": "vastai", "code": "h100-80gb", "name": "H100 80GB", "category": "gpu"},
    ]
    
    async with async_session_maker() as session:
        for s_data in skus:
            provider_code = s_data.pop("provider_code")
            result = await session.execute(
                select(Provider).where(Provider.code == provider_code)
            )
            provider = result.scalar_one_or_none()
            if provider:
                result = await session.execute(
                    select(SKU).where(SKU.provider_id == provider.id, SKU.code == s_data["code"])
                )
                if not result.scalar_one_or_none():
                    session.add(SKU(provider_id=provider.id, **s_data))
        await session.commit()
        print(f"Seeded {len(skus)} SKUs")


async def seed_price_records():
    """Seed historical price data."""
    price_data = {
        ("openai", "gpt-4o", "input"): [(30.0, -365), (15.0, -180), (5.0, -90), (2.5, 0)],
        ("openai", "gpt-4o", "output"): [(60.0, -365), (30.0, -180), (15.0, -90), (10.0, 0)],
        ("anthropic", "claude-3.5-sonnet", "input"): [(15.0, -180), (8.0, -90), (3.0, 0)],
        ("anthropic", "claude-3.5-sonnet", "output"): [(75.0, -180), (40.0, -90), (15.0, 0)],
        ("deepseek", "deepseek-v3", "input"): [(0.5, -90), (0.27, -30), (0.14, 0)],
        ("deepseek", "deepseek-v3", "output"): [(1.0, -90), (0.55, -30), (0.28, 0)],
        ("lambda", "h100-80gb", "hourly"): [(3.0, -180), (2.79, -90), (2.49, 0)],
        ("coreweave", "h100-80gb", "hourly"): [(3.2, -180), (3.0, -90), (2.85, 0)],
        ("runpod", "h100-80gb", "hourly"): [(2.8, -180), (2.59, -90), (2.39, 0)],
    }
    
    async with async_session_maker() as session:
        for (provider_code, sku_code, price_type), prices in price_data.items():
            result = await session.execute(
                select(Provider).where(Provider.code == provider_code)
            )
            provider = result.scalar_one_or_none()
            if not provider:
                continue
            
            result = await session.execute(
                select(SKU).where(SKU.provider_id == provider.id, SKU.code == sku_code)
            )
            sku = result.scalar_one_or_none()
            if not sku:
                continue
            
            for price, days_ago in prices:
                recorded_at = datetime.utcnow() + timedelta(days=days_ago)
                session.add(PriceRecord(
                    recorded_at=recorded_at,
                    provider_id=provider.id,
                    sku_id=sku.id,
                    price_type=PriceType(price_type),
                    price=Decimal(str(price)),
                    currency="USD",
                    unit="per_million_tokens" if price_type in ("input", "output") else "per_hour",
                    source_url=provider.pricing_page_url
                ))
        
        await session.commit()
        print("Seeded price records")


async def seed_supply_chain_prices():
    """Seed supply chain price data."""
    supply_data = [
        {"category": SupplyChainCategory.HBM, "item": "HBM3e-24GB", "price": 15.50, "unit": "USD/GB", "mom_change": 3.2, "yoy_change": 45.0, "source": "TrendForce"},
        {"category": SupplyChainCategory.DRAM, "item": "DDR5-4800-64GB", "price": 185.0, "unit": "USD/piece", "mom_change": -2.1, "yoy_change": -15.0, "source": "DRAMeXchange"},
        {"category": SupplyChainCategory.GPU, "item": "H100-80GB-SXM", "price": 28500.0, "unit": "USD/unit", "mom_change": 0.0, "yoy_change": -12.0, "source": "渠道调研"},
        {"category": SupplyChainCategory.PACKAGING, "item": "CoWoS利用率", "price": 98.0, "unit": "percent", "mom_change": 0.0, "yoy_change": 8.0, "source": "供应链调研"},
    ]
    
    async with async_session_maker() as session:
        for data in supply_data:
            session.add(SupplyChainPrice(recorded_at=datetime.utcnow(), **data))
        await session.commit()
        print(f"Seeded {len(supply_data)} supply chain prices")


async def seed_signals():
    """Seed sample signals."""
    signals = [
        {
            "triggered_at": datetime.utcnow() - timedelta(days=2),
            "signal_type": SignalType.PRICE_MOVE,
            "metric_id": "B4",
            "direction": "down",
            "magnitude": "-20%",
            "previous_value": Decimal("0.175"),
            "current_value": Decimal("0.14"),
            "description": "DeepSeek V3 输入价格下调 20%",
            "stage_implication": "S1维持，但增加S0风险",
            "severity": Severity.HIGH,
            "is_read": False
        },
        {
            "triggered_at": datetime.utcnow() - timedelta(days=1),
            "signal_type": SignalType.SUPPLY_CHAIN_ALERT,
            "metric_id": "E1",
            "direction": "up",
            "magnitude": "+8%",
            "description": "HBM3e价格连续3月上涨，触发成本上行预警",
            "stage_implication": "6-12月后基建成本上升",
            "severity": Severity.HIGH,
            "is_read": False
        },
    ]
    
    async with async_session_maker() as session:
        for s_data in signals:
            session.add(Signal(**s_data))
        await session.commit()
        print(f"Seeded {len(signals)} signals")


async def seed_stage_snapshot():
    """Seed current stage snapshot."""
    async with async_session_maker() as session:
        session.add(StageSnapshot(
            snapshot_at=datetime.utcnow(),
            stage=StageCode.S1,
            confidence=Confidence.MEDIUM,
            rationale="M01区间 0.24-0.36，A板块指标连续两季正增长",
            trigger_conditions={"m01_transition": True, "adoption_growing": True},
            metrics_snapshot={"m01_low": 0.24, "m01_high": 0.36}
        ))
        await session.commit()
        print("Seeded stage snapshot")


async def main():
    """Run all seed functions."""
    print("Initializing database...")
    await init_db()
    print("Seeding data...")
    await seed_providers()
    await seed_skus()
    await seed_price_records()
    await seed_supply_chain_prices()
    await seed_signals()
    await seed_stage_snapshot()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
