from collections.abc import Sequence

from sqlalchemy import Row

from src.modules.mobility.vehicles.repository import VehicleRepository
from src.modules.mobility.vehicles.schemas import (
    VehicleDetailResponse,
    VehicleNearbyResponse,
    VehicleRouteInfo,
)


class VehicleService:
    def __init__(self, repository: VehicleRepository) -> None:
        self._repository = repository

    async def get_nearby_vehicles(
        self,
        lat: float,
        lng: float,
        radius: int = 1500,
        limit: int = 200,
        route_id: str | None = None,
    ) -> list[VehicleNearbyResponse]:
        rows = await self._repository.get_nearby(lat, lng, radius, limit, route_id)
        return [self._map_nearby_row(row) for row in rows]

    async def get_vehicles_by_route(self, route_id: str, limit: int = 200) -> list[VehicleDetailResponse]:
        rows = await self._repository.get_by_route_id(route_id, limit)
        return [self._map_detail_row(row) for row in rows]

    @staticmethod
    def _map_nearby_row(row: Row) -> VehicleNearbyResponse:
        return VehicleNearbyResponse(
            id=row.id,
            prefix=row.prefix,
            lat=row.lat,
            lng=row.lng,
            is_accessible=row.is_accessible,
            last_seen_at=row.last_seen_at,
            route=VehicleRouteInfo(
                id=row.route_id,
                short_name=row.route_short_name,
                color=row.route_color,
            ),
        )

    @staticmethod
    def _map_detail_row(row: Row) -> VehicleDetailResponse:
        return VehicleDetailResponse(
            id=row.id,
            prefix=row.prefix,
            external_id=row.external_id,
            lat=row.lat,
            lng=row.lng,
            is_accessible=row.is_accessible,
            is_active=row.is_active,
            last_seen_at=row.last_seen_at,
            updated_at=row.updated_at,
            route=VehicleRouteInfo(
                id=row.route_id,
                short_name=row.route_short_name,
                color=row.route_color,
            ),
        )
