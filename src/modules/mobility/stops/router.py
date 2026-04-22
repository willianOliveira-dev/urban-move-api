import logging
from collections.abc import Sequence

from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.db.database import get_db
from src.modules.mobility.stops.controller import StopController
from src.modules.mobility.stops.repository import StopRepository
from src.modules.mobility.stops.schemas import StopResponse
from src.modules.mobility.stops.service import StopService

router = APIRouter(prefix="/stops", tags=["Stops"])
logger = logging.getLogger("urbanmove.mobility.stops")

def get_stop_controller(session: AsyncSession = Depends(get_db)) -> StopController:
    repository = StopRepository(session)
    service = StopService(repository)
    return StopController(service)

@router.get("", response_model=list[StopResponse])
async def list_stops(
    lat: float | None = Query(None, description="Latitude for nearby search"),
    lng: float | None = Query(None, description="Longitude for nearby search"),
    radius: float = Query(500.0, ge=100.0, le=5000.0, description="Search radius in meters"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    controller: StopController = Depends(get_stop_controller),
) -> Sequence[StopResponse]:
    if lat is not None and lng is not None:
        return await controller.get_nearby_stops(lat=lat, lng=lng, radius=radius, limit=limit)
    return await controller.get_stops(limit=limit, offset=offset)

@router.get("/{stop_id}", response_model=StopResponse)
async def get_stop(
    stop_id: str,
    controller: StopController = Depends(get_stop_controller),
) -> StopResponse:
    return await controller.get_stop(stop_id)
