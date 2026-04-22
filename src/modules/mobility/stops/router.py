import logging
from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_db
from src.modules.mobility.stops.controller import StopController
from src.modules.mobility.stops.repository import StopRepository
from src.modules.mobility.stops.schemas import NearbyStopResponse, StopArrivalsResponse, StopResponse
from src.modules.mobility.stops.service import StopNotFoundError, StopService

router = APIRouter(prefix="/stops", tags=["Stops"])
logger = logging.getLogger("urbanmove.mobility.stops")


def get_stop_controller(session: AsyncSession = Depends(get_db)) -> StopController:
    repository = StopRepository(session)
    service = StopService(repository)
    return StopController(service)


@router.get("/nearby", response_model=list[NearbyStopResponse])
async def get_nearby_stops(
    lat: float = Query(..., ge=-90, le=90, description="Latitude do usuário"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude do usuário"),
    radius: float = Query(500.0, ge=100.0, le=5000.0, description="Raio em metros"),
    limit: int = Query(20, ge=1, le=100),
    controller: StopController = Depends(get_stop_controller),
) -> list[NearbyStopResponse]:
    return await controller.get_nearby_stops(lat=lat, lng=lng, radius=radius, limit=limit)


@router.get("/{stop_id}", response_model=StopResponse)
async def get_stop(
    stop_id: str,
    controller: StopController = Depends(get_stop_controller),
) -> StopResponse:
    try:
        return await controller.get_stop(stop_id)
    except StopNotFoundError:
        raise HTTPException(status_code=404, detail=f"Parada '{stop_id}' não encontrada.")


@router.get("/{stop_id}/arrivals", response_model=StopArrivalsResponse)
async def get_stop_arrivals(
    stop_id: str,
    controller: StopController = Depends(get_stop_controller),
) -> StopArrivalsResponse:
    try:
        return await controller.get_arrivals(stop_id)
    except StopNotFoundError:
        raise HTTPException(status_code=404, detail=f"Parada '{stop_id}' não encontrada.")


@router.get("", response_model=list[StopResponse])
async def list_stops(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    controller: StopController = Depends(get_stop_controller),
) -> Sequence[StopResponse]:
    return await controller.get_stops(limit=limit, offset=offset)
