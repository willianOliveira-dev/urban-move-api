from collections.abc import Sequence

from src.core.db.models.stop import Stop
from src.modules.mobility.stops.repository import StopRepository

class StopService:
    def __init__(self, repository: StopRepository) -> None:
        self.repository = repository

    async def list_active_stops(self, limit: int = 100, offset: int = 0) -> Sequence[Stop]:
        return await self.repository.get_all_stops(limit=limit, offset=offset)

    async def search_nearby_stops(self, lat: float, lng: float, radius: float, limit: int) -> Sequence[Stop]:
        return await self.repository.get_stops_nearby(lat=lat, lng=lng, radius_meters=radius, limit=limit)

    async def get_stop(self, stop_id: str) -> Stop | None:
        return await self.repository.get_stop_by_id(stop_id)
