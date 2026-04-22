import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.database import get_db
from src.modules.mobility.search.schemas import SearchResponse
from src.modules.mobility.search.service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])
logger = logging.getLogger("urbanmove.mobility.search")


def get_search_service(session: AsyncSession = Depends(get_db)) -> SearchService:
    return SearchService(session)


@router.get("", response_model=SearchResponse)
async def search_mobility(
    q: str = Query(..., min_length=2, max_length=100, description="Termo de busca"),
    limit: int = Query(10, ge=1, le=50),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    return await service.search(query=q, limit=limit)
