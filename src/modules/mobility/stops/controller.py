from collections.abc import Sequence

from src.core.db.models.stop import Stop
from src.modules.mobility.stops.schemas import NearbyStopResponse, StopArrivalsResponse
from src.modules.mobility.stops.service import StopService


class StopController:
    def __init__(self, service: StopService) -> None:
        self._service = service

    async def get_stops(self, limit: int = 100, offset: int = 0) -> Sequence[Stop]:
        return await self._service.get_stops(limit=limit, offset=offset)

    async def get_stop(self, stop_id: str) -> Stop:
        return await self._service.get_stop(stop_id)

    async def get_nearby_stops(
        self,
        lat: float,
        lng: float,
        radius: float = 500.0,
        limit: int = 20,
    ) -> list[NearbyStopResponse]:
        return await self._service.get_nearby_stops(lat=lat, lng=lng, radius=radius, limit=limit)

    async def get_arrivals(self, stop_id: str) -> StopArrivalsResponse:
        return await self._service.get_arrivals(stop_id)
