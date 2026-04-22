from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehicleRouteInfo(BaseModel):
    id: str = Field(..., description="UUID da rota")
    short_name: str = Field(..., description="Letreiro curto (ex: 6505-10)")
    color: str = Field(..., description="Cor hex da rota")

    model_config = ConfigDict(from_attributes=True)


class VehicleNearbyResponse(BaseModel):
    id: str = Field(..., description="UUID do veículo")
    prefix: str = Field(..., description="Prefixo do veículo")
    lat: float = Field(..., description="Latitude atual")
    lng: float = Field(..., description="Longitude atual")
    is_accessible: bool = Field(..., description="Acessibilidade")
    last_seen_at: datetime = Field(..., description="Última atualização de posição")
    route: VehicleRouteInfo = Field(..., description="Informações da rota")


class VehicleDetailResponse(BaseModel):
    id: str
    prefix: str
    external_id: str
    lat: float
    lng: float
    is_accessible: bool
    is_active: bool
    last_seen_at: datetime
    updated_at: datetime
    route: VehicleRouteInfo

    model_config = ConfigDict(from_attributes=True)
