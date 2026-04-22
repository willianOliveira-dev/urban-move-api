from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TripPreference = Literal["fastest", "cheapest", "eco"]


class TripPlanRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "origin_lat": -23.550520,
                    "origin_lng": -46.633308,
                    "destination_lat": -23.582846,
                    "destination_lng": -46.685366,
                    "preference": "fastest",
                }
            ]
        }
    )

    origin_lat: float = Field(..., ge=-90, le=90, description="Latitude de origem")
    origin_lng: float = Field(..., ge=-180, le=180, description="Longitude de origem")
    destination_lat: float = Field(..., ge=-90, le=90, description="Latitude de destino")
    destination_lng: float = Field(..., ge=-180, le=180, description="Longitude de destino")
    preference: TripPreference = Field(
        default="fastest",
        description="Critério de ordenação: fastest, cheapest ou eco",
    )


class TripStepTransitDetails(BaseModel):
    line_name: str = Field(..., description="Nome/letreiro da linha")
    line_color: str = Field(default="#0066CC", description="Cor da linha")
    line_vehicle_type: str = Field(default="BUS", description="Tipo (BUS, METRO, TRAM, etc.)")
    departure_stop: str = Field(..., description="Parada de embarque")
    arrival_stop: str = Field(..., description="Parada de desembarque")
    num_stops: int = Field(default=0, description="Número de paradas no trecho")
    headsign: str = Field(default="", description="Destino/direção da linha")


class TripStep(BaseModel):
    type: str = Field(..., description="WALKING ou TRANSIT")
    instruction: str = Field(..., description="Instrução legível para o usuário")
    distance_meters: int = Field(default=0, description="Distância do trecho em metros")
    distance_text: str = Field(default="", description="Distância formatada (ex: 200m)")
    duration_seconds: int = Field(default=0, description="Duração do trecho em segundos")
    duration_text: str = Field(default="", description="Duração formatada (ex: 3 min)")
    start_location: dict[str, float] = Field(default_factory=dict, description="Ponto de início {lat, lng}")
    end_location: dict[str, float] = Field(default_factory=dict, description="Ponto de fim {lat, lng}")
    polyline: str = Field(default="", description="Polyline codificada do trecho")
    transit_details: TripStepTransitDetails | None = Field(None, description="Detalhes do transporte público")


class TripMainLine(BaseModel):
    name: str = Field(..., description="Nome curto da linha (ex: BRT T3, L4)")
    color: str = Field(..., description="Cor da linha")
    vehicle_type: str = Field(..., description="Modal (BUS, METRO, etc)")


class TripOption(BaseModel):
    summary: str = Field(..., description="Resumo (ex: Centro — Ipanema)")
    total_duration_seconds: int = Field(..., description="Duração total em segundos")
    total_duration_text: str = Field(..., description="Duração formatada")
    total_distance_meters: int = Field(default=0, description="Distância total em metros")
    departure_time: str = Field(default="", description="Horário de saída")
    arrival_time: str = Field(default="", description="Horário de chegada prevista")
    fare_text: str | None = Field(None, description="Tarifa formatada (ex: R$ 4,60)")
    fare_value: float | None = Field(None, description="Tarifa em reais")
    transfers: int = Field(default=0, description="Número de baldeações")
    main_lines: list[TripMainLine] = Field(default_factory=list, description="Linhas de transporte utilizadas")
    steps: list[TripStep] = Field(default_factory=list, description="Passos da rota")


class TripPlanResponse(BaseModel):
    origin: str = Field(default="", description="Endereço de origem resolvido")
    destination: str = Field(default="", description="Endereço de destino resolvido")
    options: list[TripOption] = Field(default_factory=list, description="Opções de rota ordenadas pelo filtro")
