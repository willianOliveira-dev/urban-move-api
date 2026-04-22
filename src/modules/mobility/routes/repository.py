from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.models.route import Route

class RouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_routes(self, limit: int = 100, offset: int = 0) -> Sequence[Route]:
        query = select(Route).where(Route.is_active.is_(True)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_route_by_id(self, route_id: str) -> Route | None:
        query = select(Route).where(Route.id == route_id)
        result = await self.session.execute(query)
        return result.scalars().first()
