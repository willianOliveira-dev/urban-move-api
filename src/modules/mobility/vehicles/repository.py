from collections.abc import Sequence

from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_X, ST_Y
from sqlalchemy import Row, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.models.route import Route
from src.core.db.models.vehicle import Vehicle


class VehicleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_nearby(
        self,
        lat: float,
        lng: float,
        radius: int = 1500,
        limit: int = 200,
        route_id: str | None = None,
    ) -> Sequence[Row]:
        point = func.ST_GeographyFromText(f"SRID=4326;POINT({lng} {lat})")
        geom = cast(Vehicle.current_location, Geometry)

        query = (
            select(
                Vehicle.id,
                Vehicle.prefix,
                Vehicle.is_accessible,
                Vehicle.last_seen_at,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
                Route.id.label("route_id"),
                Route.short_name.label("route_short_name"),
                Route.color.label("route_color"),
            )
            .join(Route, Vehicle.route_id == Route.id)
            .where(Vehicle.is_active.is_(True))
            .where(ST_DWithin(Vehicle.current_location, point, radius))
            .order_by(ST_Distance(Vehicle.current_location, point))
            .limit(limit)
        )

        if route_id:
            query = query.where(Vehicle.route_id == route_id)

        result = await self._session.execute(query)
        return result.all()

    async def get_by_route_id(self, route_id: str, limit: int = 200) -> Sequence[Row]:
        geom = cast(Vehicle.current_location, Geometry)

        query = (
            select(
                Vehicle.id,
                Vehicle.prefix,
                Vehicle.external_id,
                Vehicle.is_accessible,
                Vehicle.is_active,
                Vehicle.last_seen_at,
                Vehicle.updated_at,
                ST_Y(geom).label("lat"),
                ST_X(geom).label("lng"),
                Route.id.label("route_id"),
                Route.short_name.label("route_short_name"),
                Route.color.label("route_color"),
            )
            .join(Route, Vehicle.route_id == Route.id)
            .where(Vehicle.is_active.is_(True))
            .where(Vehicle.route_id == route_id)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return result.all()
