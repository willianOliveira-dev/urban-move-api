from collections.abc import Sequence

from fastapi import HTTPException

from src.core.db.models.stop import Stop
from src.modules.mobility.stops.service import StopService

class StopController:
    def __init__(self, service: StopService) -> None:
        self.service = service

    async def get_stops(self, limit: int = 100, offset: int = 0) -> Sequence[Stop]:
        return await self.service.list_active_stops(limit=limit, offset=offset)

    async def get_nearby_stops(self, lat: float, lng: float, radius: float, limit: int) -> Sequence[Stop]:
        return await self.service.search_nearby_stops(lat=lat, lng=lng, radius=radius, limit=limit)

    async def get_stop(self, stop_id: str) -> Stop:
        stop = await self.service.get_stop(stop_id)
        if not stop:
            raise HTTPException(status_code=404, detail="Stop not found")
        return stop
