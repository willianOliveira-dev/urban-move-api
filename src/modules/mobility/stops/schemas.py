from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.core.db.models.enums import TransportModal


class StopResponse(BaseModel):
    id: str = Field(..., description="UUID da parada")
    external_id: str = Field(..., description="ID externo SPTrans")
    name: str = Field(..., description="Nome da parada")
    modal: TransportModal = Field(..., description="Modal de transporte")
    has_shelter: bool | None = Field(None, description="Possui abrigo")
    is_accessible: bool = Field(..., description="Parada acessível")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NearbyStopResponse(BaseModel):
    id: str = Field(..., description="UUID da parada")
    external_id: str = Field(..., description="ID externo SPTrans")
    name: str = Field(..., description="Nome da parada")
    modal: TransportModal = Field(..., description="Modal de transporte")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    distance_meters: float = Field(..., description="Distância em metros do ponto de referência")
    is_accessible: bool = Field(..., description="Acessibilidade")


class ArrivalInfo(BaseModel):
    route_short_name: str = Field(..., description="Letreiro da linha (ex: 474)")
    route_color: str = Field(default="#0066CC", description="Cor da linha")
    destination: str = Field(..., description="Destino (letreiro secundário)")
    eta_minutes: int = Field(..., description="Tempo estimado de chegada em minutos")
    vehicle_prefix: str = Field(..., description="Prefixo do veículo")
    is_accessible: bool = Field(..., description="Veículo acessível")


class StopArrivalsResponse(BaseModel):
    stop_id: str = Field(..., description="UUID da parada")
    stop_name: str = Field(..., description="Nome da parada")
    arrivals: list[ArrivalInfo] = Field(default_factory=list, description="Previsões de chegada")
