from collections.abc import Sequence

from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_X, ST_Y
from sqlalchemy import Row, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.models.stop import Stop


class StopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[Stop]:
        query = select(Stop).limit(limit).offset(offset)
        result = await self._session.execute(query)
        return result.scalars().all()

    async def get_nearby(
        self,
        lat: float,
        lng: float,
        radius_meters: float = 500.0,
        limit: int = 20,
    ) -> Sequence[Row]:
        ref_geog = func.ST_GeographyFromText(f"SRID=4326;POINT({lng} {lat})")
        geom = cast(Stop.location, Geometry)

        query = (
            select(
                Stop.id,
                Stop.external_id,
                Stop.name,
                Stop.modal,
                Stop.is_accessible,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
                ST_Distance(Stop.location, ref_geog).label("distance_meters"),
            )
            .where(ST_DWithin(Stop.location, ref_geog, radius_meters))
            .order_by(ST_Distance(Stop.location, ref_geog))
            .limit(limit)
        )
        result = await self._session.execute(query)
        return result.all()

    async def get_by_id(self, stop_id: str) -> Stop | None:
        query = select(Stop).where(Stop.id == stop_id)
        result = await self._session.execute(query)
        return result.scalars().first()

    async def get_by_external_id(self, external_id: str) -> Stop | None:
        query = select(Stop).where(Stop.external_id == external_id)
        result = await self._session.execute(query)
        return result.scalars().first()
