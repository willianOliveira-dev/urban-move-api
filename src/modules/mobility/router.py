from fastapi import APIRouter

from src.modules.mobility.routes.router import router as routes_router
from src.modules.mobility.stops.router import router as stops_router
from src.modules.mobility.sptrans.router import router as sptrans_router

router = APIRouter(prefix="/api/v1/mobility")

router.include_router(routes_router)
router.include_router(stops_router)
router.include_router(sptrans_router)
