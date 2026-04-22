from pydantic import BaseModel, Field

from src.core.db.models.enums import TransportModal


class SearchRouteResult(BaseModel):
    id: str
    short_name: str
    long_name: str
    color: str


class SearchStopResult(BaseModel):
    id: str
    name: str
    modal: TransportModal


class SearchResponse(BaseModel):
    routes: list[SearchRouteResult] = Field(default_factory=list)
    stops: list[SearchStopResult] = Field(default_factory=list)
