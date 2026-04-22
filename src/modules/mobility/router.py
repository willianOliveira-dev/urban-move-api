from fastapi import APIRouter, Depends
from src.modules.auth.dependencies import get_current_user_id
from src.modules.mobility.routes.router import router as routes_router
from src.modules.mobility.search.router import router as search_router
from src.modules.mobility.sptrans.router import router as sptrans_router
from src.modules.mobility.stops.router import router as stops_router
from src.modules.mobility.trips.router import router as trips_router
from src.modules.mobility.vehicles.router import router as vehicles_router

router = APIRouter(
    prefix="/api/v1/mobility",
    dependencies=[Depends(get_current_user_id)],
)

router.include_router(routes_router)
router.include_router(stops_router)
router.include_router(vehicles_router)
router.include_router(trips_router)
router.include_router(search_router)
router.include_router(sptrans_router)
