import logging

from fastapi import APIRouter, Depends, HTTPException, status

from src.core.db.database import get_redis
from src.modules.mobility.trips.schemas import TripPlanRequest, TripPlanResponse
from src.modules.mobility.trips.service import TRIP_CACHE_TTL_SECONDS, TripPlanError, TripPlanService
from src.shared.cache import CacheService

router = APIRouter(prefix="/trips", tags=["Trip Planner"])
logger = logging.getLogger("urbanmove.mobility.trips")


def get_trip_service() -> TripPlanService:
    redis_client = get_redis()
    cache = CacheService(
        redis_client=redis_client,
        prefix="trips:plan",
        ttl_seconds=TRIP_CACHE_TTL_SECONDS,
    )
    return TripPlanService(cache=cache)


@router.post("/plan", response_model=TripPlanResponse)
async def plan_trip(
    request: TripPlanRequest,
    service: TripPlanService = Depends(get_trip_service),
) -> TripPlanResponse:
    try:
        return await service.plan(request)
    except TripPlanError as e:
        logger.error({"event": "trip_plan_failed", "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        ) from e
