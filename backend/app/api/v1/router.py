"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.prices import router as prices_router
from app.api.v1.signals import router as signals_router
from app.api.v1.stage import router as stage_router
from app.api.v1.supply_chain import router as supply_chain_router
from app.api.v1.config import router as config_router
from app.api.v1.data import router as data_router
from app.api.v1.price_indices import router as price_indices_router
from app.api.v1.financials import router as financials_router
from app.api.v1.collected_data import router as collected_data_router

router = APIRouter(prefix="/v1")

router.include_router(prices_router)
router.include_router(signals_router)
router.include_router(stage_router)
router.include_router(supply_chain_router)
router.include_router(config_router)
router.include_router(data_router)
router.include_router(price_indices_router)
router.include_router(financials_router)
router.include_router(collected_data_router)

