import logging
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import Row

from src.core.db.models.stop import Stop
from src.modules.mobility.sptrans.service import SPTransClient, SPTransClientError
from src.modules.mobility.stops.repository import StopRepository
from src.modules.mobility.stops.schemas import (
    ArrivalInfo,
    NearbyStopResponse,
    StopArrivalsResponse,
)

logger = logging.getLogger("urbanmove.mobility.stops")


class StopNotFoundError(Exception):
    """Exceção de domínio para parada não encontrada."""

    def __init__(self, stop_id: str) -> None:
        super().__init__(f"Parada não encontrada: {stop_id}")
        self.stop_id = stop_id


class StopService:
    def __init__(self, repository: StopRepository) -> None:
        self._repository = repository

    async def get_stops(self, limit: int = 100, offset: int = 0) -> Sequence[Stop]:
        return await self._repository.get_all(limit=limit, offset=offset)

    async def get_stop(self, stop_id: str) -> Stop:
        stop = await self._repository.get_by_id(stop_id)
        if stop is None:
            raise StopNotFoundError(stop_id)
        return stop

    async def get_nearby_stops(
        self,
        lat: float,
        lng: float,
        radius: float = 500.0,
        limit: int = 20,
    ) -> list[NearbyStopResponse]:
        rows = await self._repository.get_nearby(lat, lng, radius, limit)
        return [self._map_nearby_row(row) for row in rows]

    async def get_arrivals(self, stop_id: str) -> StopArrivalsResponse:
        """Busca previsões de chegada em tempo real via SPTrans."""
        stop = await self._repository.get_by_id(stop_id)
        if stop is None:
            raise StopNotFoundError(stop_id)

        client = SPTransClient()
        try:
            predictions = await client.get_stop_predictions(stop.external_id)
            arrivals = self._parse_sptrans_predictions(predictions)

            return StopArrivalsResponse(
                stop_id=stop_id,
                stop_name=stop.name,
                arrivals=arrivals,
            )
        except SPTransClientError as e:
            logger.error(
                {"event": "sptrans.predictions.failed", "stop_id": stop_id, "error": str(e)}
            )
            return StopArrivalsResponse(stop_id=stop_id, stop_name=stop.name, arrivals=[])
        finally:
            await client.close()

    @staticmethod
    def _parse_sptrans_predictions(data: dict[str, object]) -> list[ArrivalInfo]:
        """Transforma a resposta da SPTrans /Previsao/Parada no formato UrbanMove."""
        arrivals: list[ArrivalInfo] = []
        now = datetime.now(timezone.utc)

        parada = data.get("p", {})
        lines = parada.get("l", []) if isinstance(parada, dict) else []

        for line in lines:
            if not isinstance(line, dict):
                continue

            short_name = str(line.get("c", ""))
            destination = str(line.get("lt1", ""))

            vehicles = line.get("vs", [])
            if not isinstance(vehicles, list):
                continue

            for v in vehicles:
                if not isinstance(v, dict):
                    continue

                ta = v.get("t", "")
                prefix = str(v.get("p", ""))
                accessible = bool(v.get("a", False))

                eta_minutes = _parse_eta_minutes(str(ta), now)

                arrivals.append(
                    ArrivalInfo(
                        route_short_name=short_name,
                        destination=destination or "Destino",
                        eta_minutes=eta_minutes,
                        vehicle_prefix=prefix,
                        is_accessible=accessible,
                    )
                )

        arrivals.sort(key=lambda a: a.eta_minutes)
        return arrivals

    @staticmethod
    def _map_nearby_row(row: Row) -> NearbyStopResponse:
        return NearbyStopResponse(
            id=row.id,
            external_id=row.external_id,
            name=row.name,
            modal=row.modal,
            lat=row.lat,
            lng=row.lng,
            distance_meters=round(row.distance_meters, 1),
            is_accessible=row.is_accessible,
        )


def _parse_eta_minutes(raw_timestamp: str, now: datetime) -> int:
    """Calcula minutos restantes a partir do timestamp ISO da SPTrans."""
    try:
        eta_dt = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
        return max(0, int((eta_dt - now).total_seconds() / 60))
    except (ValueError, TypeError, AttributeError):
        return 0
