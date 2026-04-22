import logging
from collections.abc import Sequence

from fastapi import APIRouter, Depends, Query

from src.core.db.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.mobility.routes.controller import RouteController
from src.modules.mobility.routes.repository import RouteRepository
from src.modules.mobility.routes.schemas import RouteResponse
from src.modules.mobility.routes.service import RouteService

router = APIRouter(prefix="/routes", tags=["Routes"])
logger = logging.getLogger("urbanmove.mobility.routes")

def get_route_controller(session: AsyncSession = Depends(get_db_session)) -> RouteController:
    repository = RouteRepository(session)
    service = RouteService(repository)
    return RouteController(service)

@router.get("", response_model=list[RouteResponse])
async def list_routes(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    controller: RouteController = Depends(get_route_controller),
) -> Sequence[RouteResponse]:
    return await controller.get_routes(limit=limit, offset=offset)

@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: str,
    controller: RouteController = Depends(get_route_controller),
) -> RouteResponse:
    return await controller.get_route(route_id)
