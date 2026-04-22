from collections.abc import Sequence

from src.core.db.models.route import Route
from src.modules.mobility.routes.repository import RouteRepository

class RouteService:
    def __init__(self, repository: RouteRepository) -> None:
        self.repository = repository

    async def list_active_routes(self, limit: int = 100, offset: int = 0) -> Sequence[Route]:
        return await self.repository.get_all_routes(limit=limit, offset=offset)

    async def get_route(self, route_id: str) -> Route | None:
        return await self.repository.get_route_by_id(route_id)
