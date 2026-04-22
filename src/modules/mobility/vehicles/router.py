import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_db
from src.modules.mobility.vehicles.repository import VehicleRepository
from src.modules.mobility.vehicles.schemas import VehicleDetailResponse, VehicleNearbyResponse
from src.modules.mobility.vehicles.service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])
logger = logging.getLogger("urbanmove.mobility.vehicles")


def get_vehicle_service(session: AsyncSession = Depends(get_db)) -> VehicleService:
    return VehicleService(VehicleRepository(session))


@router.get("/nearby", response_model=list[VehicleNearbyResponse])
async def get_nearby_vehicles(
    lat: float = Query(..., ge=-90, le=90, description="Latitude do centro do mapa"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude do centro do mapa"),
    radius: int = Query(1500, ge=100, le=5000, description="Raio em metros"),
    route_id: str | None = Query(None, description="Filtrar por rota específica"),
    limit: int = Query(200, ge=1, le=500, description="Máximo de veículos"),
    service: VehicleService = Depends(get_vehicle_service),
) -> list[VehicleNearbyResponse]:
    return await service.get_nearby_vehicles(lat=lat, lng=lng, radius=radius, limit=limit, route_id=route_id)


@router.get("/by-route/{route_id}", response_model=list[VehicleDetailResponse])
async def get_vehicles_by_route(
    route_id: str,
    limit: int = Query(200, ge=1, le=500),
    service: VehicleService = Depends(get_vehicle_service),
) -> list[VehicleDetailResponse]:
    return await service.get_vehicles_by_route(route_id=route_id, limit=limit)
