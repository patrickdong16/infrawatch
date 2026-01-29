"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.prices import router as prices_router
from app.api.v1.signals import router as signals_router
from app.api.v1.stage import router as stage_router
from app.api.v1.supply_chain import router as supply_chain_router
from app.api.v1.config import router as config_router
from app.api.v1.data import router as data_router

router = APIRouter(prefix="/v1")

router.include_router(prices_router)
router.include_router(signals_router)
router.include_router(stage_router)
router.include_router(supply_chain_router)
router.include_router(config_router)
router.include_router(data_router)

