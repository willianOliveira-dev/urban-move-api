from collections.abc import Sequence

from fastapi import HTTPException

from src.core.db.models.route import Route
from src.modules.mobility.routes.service import RouteService

class RouteController:
    def __init__(self, service: RouteService) -> None:
        self.service = service

    async def get_routes(self, limit: int = 100, offset: int = 0) -> Sequence[Route]:
        return await self.service.list_active_routes(limit=limit, offset=offset)

    async def get_route(self, route_id: str) -> Route:
        route = await self.service.get_route(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        return route
