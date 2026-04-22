from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.models.route import Route
from src.core.db.models.stop import Stop
from src.modules.mobility.search.schemas import SearchResponse, SearchRouteResult, SearchStopResult


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(self, query: str, limit: int = 10) -> SearchResponse:
        term = f"%{query}%"

        routes_query = (
            select(Route.id, Route.short_name, Route.long_name, Route.color)
            .where(Route.is_active.is_(True))
            .where(
                func.concat(Route.short_name, " ", Route.long_name).ilike(term)
            )
            .limit(limit)
        )
        routes_result = await self._session.execute(routes_query)
        routes = [
            SearchRouteResult(
                id=r.id,
                short_name=r.short_name,
                long_name=r.long_name or "",
                color=r.color or "#0066CC",
            )
            for r in routes_result.all()
        ]

        stops_query = (
            select(Stop.id, Stop.name, Stop.modal)
            .where(Stop.name.ilike(term))
            .limit(limit)
        )
        stops_result = await self._session.execute(stops_query)
        stops = [
            SearchStopResult(id=s.id, name=s.name, modal=s.modal)
            for s in stops_result.all()
        ]

        return SearchResponse(routes=routes, stops=stops)
