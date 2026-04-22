from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from src.core.db.models.stop import Stop

class StopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_stops(self, limit: int = 100, offset: int = 0) -> Sequence[Stop]:
        query = select(Stop).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_stops_nearby(self, lat: float, lng: float, radius_meters: float = 500.0, limit: int = 50) -> Sequence[Stop]:
        # Using PostGIS ST_DWithin on geography type
        # SRID 4326, ST_Point(lon, lat)
        point = f"SRID=4326;POINT({lng} {lat})"
        query = (
            select(Stop)
            .where(func.ST_DWithin(Stop.location, func.ST_GeographyFromText(point), radius_meters))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_stop_by_id(self, stop_id: str) -> Stop | None:
        query = select(Stop).where(Stop.id == stop_id)
        result = await self.session.execute(query)
        return result.scalars().first()
