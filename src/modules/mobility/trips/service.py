import logging

import httpx

from src.core.config.env import env
from src.modules.mobility.trips.schemas import (
    TripMainLine,
    TripOption,
    TripPlanRequest,
    TripPlanResponse,
    TripPreference,
    TripStep,
    TripStepTransitDetails,
)
from src.shared.cache import CacheService

logger = logging.getLogger("urbanmove.mobility.trips")

GOOGLE_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"

VEHICLE_TYPE_MAP: dict[str, str] = {
    "BUS": "BUS",
    "SUBWAY": "METRO",
    "METRO_RAIL": "METRO",
    "RAIL": "TRAIN",
    "TRAM": "VLT",
    "HEAVY_RAIL": "TRAIN",
    "COMMUTER_TRAIN": "TRAIN",
    "FERRY": "FERRY",
}

TRIP_CACHE_TTL_SECONDS = 300  


def _safe_get(data: object, *keys: str, default: object = "") -> object:
    """Navega de forma segura por dicts aninhados sem usar Any."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def _safe_str(value: object, fallback: str = "") -> str:
    return str(value) if value is not None else fallback


def _safe_int(value: object, fallback: int = 0) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        try:
            return int(value)
        except (ValueError, TypeError):
            return fallback
    return fallback


def _safe_float(value: object, fallback: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return fallback
    return fallback


class TripPlanError(Exception):
    """Exceção de domínio para falhas no planejamento de rotas."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.name = "TripPlanError"


class TripPlanService:
    """Proxy para o Google Directions API no modo transit, com cache Redis."""

    def __init__(self, cache: CacheService | None = None) -> None:
        self._cache = cache

    async def plan(self, request: TripPlanRequest) -> TripPlanResponse:
        cache_key = self._build_cache_key(request)

        cached = await self._get_from_cache(cache_key)
        if cached is not None:
            logger.info({"event": "trip.cache.hit", "key": cache_key[:32]})
            return self._build_response_from_cache(cached, request.preference)

        data = await self._fetch_directions(request)

        status = _safe_str(data.get("status"))

        if status == "ZERO_RESULTS":
            return TripPlanResponse(options=[])
        if status != "OK":
            logger.error({"event": "google.directions.error", "status": status})
            raise TripPlanError(f"Erro na API de rotas: {status}")

        routes = data.get("routes", [])
        if not isinstance(routes, list) or not routes:
            return TripPlanResponse(options=[])

        first_leg = _safe_get(routes[0], "legs")
        first_leg_data = first_leg[0] if isinstance(first_leg, list) and first_leg else {}

        origin_address = _safe_str(_safe_get(first_leg_data, "start_address"))
        destination_address = _safe_str(_safe_get(first_leg_data, "end_address"))

        options = [self._parse_route(route) for route in routes if isinstance(route, dict)]

        await self._save_to_cache(cache_key, origin_address, destination_address, options)

        self._sort_by_preference(options, request.preference)

        return TripPlanResponse(
            origin=origin_address,
            destination=destination_address,
            options=options,
        )

    def _build_cache_key(self, request: TripPlanRequest) -> str:
        """Gera chave de cache baseada apenas em origem/destino (independente do filtro)."""
        return (
            f"{request.origin_lat:.5f},{request.origin_lng:.5f}"
            f"->{request.destination_lat:.5f},{request.destination_lng:.5f}"
        )

    async def _get_from_cache(self, cache_key: str) -> dict[str, object] | None:
        if self._cache is None:
            return None
        return await self._cache.get(cache_key)

    async def _save_to_cache(
        self,
        cache_key: str,
        origin: str,
        destination: str,
        options: list[TripOption],
    ) -> None:
        if self._cache is None:
            return
        payload: dict[str, object] = {
            "origin": origin,
            "destination": destination,
            "options": [opt.model_dump() for opt in options],
        }
        await self._cache.set(cache_key, payload)

    def _build_response_from_cache(
        self,
        cached: dict[str, object],
        preference: TripPreference,
    ) -> TripPlanResponse:
        """Reconstrói a resposta do cache e aplica a ordenação do filtro atual."""
        raw_options = cached.get("options", [])
        option_list = raw_options if isinstance(raw_options, list) else []
        options = [TripOption.model_validate(opt) for opt in option_list]
        self._sort_by_preference(options, preference)
        return TripPlanResponse(
            origin=_safe_str(cached.get("origin", "")),
            destination=_safe_str(cached.get("destination", "")),
            options=options,
        )

    async def _fetch_directions(self, request: TripPlanRequest) -> dict[str, object]:
        params: dict[str, str] = {
            "origin": f"{request.origin_lat},{request.origin_lng}",
            "destination": f"{request.destination_lat},{request.destination_lng}",
            "mode": "transit",
            "alternatives": "true",
            "language": "pt-BR",
            "region": "br",
            "key": env.GOOGLE_MAPS_API_KEY,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(GOOGLE_DIRECTIONS_URL, params=params)
                response.raise_for_status()
                result: dict[str, object] = response.json()
                return result
            except httpx.RequestError as e:
                logger.error({"event": "google.directions.request_failed", "error": str(e)})
                raise TripPlanError("Falha ao comunicar com o serviço de rotas.") from e

    def _sort_by_preference(self, options: list[TripOption], preference: TripPreference) -> None:
        if preference == "cheapest":
            options.sort(key=lambda o: o.fare_value if o.fare_value is not None else float("inf"))
        elif preference == "eco":
            options.sort(key=lambda o: (o.transfers, o.total_duration_seconds))
        else:
            options.sort(key=lambda o: o.total_duration_seconds)

    def _parse_route(self, route: dict[str, object]) -> TripOption:
        legs = route.get("legs", [])
        leg = legs[0] if isinstance(legs, list) and legs else {}
        if not isinstance(leg, dict):
            leg = {}

        raw_steps = leg.get("steps", [])
        step_list = raw_steps if isinstance(raw_steps, list) else []
        steps = [self._parse_step(s) for s in step_list if isinstance(s, dict)]

        transit_steps = [s for s in steps if s.type == "TRANSIT"]
        transfers = max(0, len(transit_steps) - 1)

        fare = route.get("fare", {})
        fare_dict = fare if isinstance(fare, dict) else {}

        main_lines = self._extract_main_lines(transit_steps)

        start_addr = _safe_str(_safe_get(leg, "start_address")).split(",")[0]
        end_addr = _safe_str(_safe_get(leg, "end_address")).split(",")[0]

        fare_text_raw = fare_dict.get("text")
        fare_value_raw = fare_dict.get("value")

        return TripOption(
            summary=f"{start_addr} — {end_addr}",
            total_duration_seconds=_safe_int(_safe_get(leg, "duration", "value", default=0)),
            total_duration_text=_safe_str(_safe_get(leg, "duration", "text")),
            total_distance_meters=_safe_int(_safe_get(leg, "distance", "value", default=0)),
            departure_time=_safe_str(_safe_get(leg, "departure_time", "text")),
            arrival_time=_safe_str(_safe_get(leg, "arrival_time", "text")),
            fare_text=_safe_str(fare_text_raw) if fare_text_raw is not None else None,
            fare_value=_safe_float(fare_value_raw) if fare_value_raw is not None else None,
            transfers=transfers,
            main_lines=main_lines,
            steps=steps,
        )

    def _extract_main_lines(self, transit_steps: list[TripStep]) -> list[TripMainLine]:
        lines: list[TripMainLine] = []
        for ts in transit_steps:
            if ts.transit_details:
                lines.append(
                    TripMainLine(
                        name=ts.transit_details.line_name,
                        color=ts.transit_details.line_color,
                        vehicle_type=ts.transit_details.line_vehicle_type,
                    )
                )
        return lines

    def _parse_step(self, step: dict[str, object]) -> TripStep:
        travel_mode = _safe_str(step.get("travel_mode", "WALKING"))
        instruction = self._sanitize_html_instruction(
            _safe_str(step.get("html_instructions", ""))
        )

        base = TripStep(
            type=travel_mode,
            instruction=instruction,
            distance_meters=_safe_int(_safe_get(step, "distance", "value", default=0)),
            distance_text=_safe_str(_safe_get(step, "distance", "text")),
            duration_seconds=_safe_int(_safe_get(step, "duration", "value", default=0)),
            duration_text=_safe_str(_safe_get(step, "duration", "text")),
            start_location={
                "lat": _safe_float(_safe_get(step, "start_location", "lat", default=0.0)),
                "lng": _safe_float(_safe_get(step, "start_location", "lng", default=0.0)),
            },
            end_location={
                "lat": _safe_float(_safe_get(step, "end_location", "lat", default=0.0)),
                "lng": _safe_float(_safe_get(step, "end_location", "lng", default=0.0)),
            },
            polyline=_safe_str(_safe_get(step, "polyline", "points")),
        )

        if travel_mode == "TRANSIT":
            self._enrich_transit_details(base, step)

        return base

    def _sanitize_html_instruction(self, raw_html: str) -> str:
        text = raw_html.replace("<b>", "").replace("</b>", "")
        text = text.replace('<div style="font-size:0.9em">', " — ")
        text = text.replace("</div>", "")
        text = text.replace("<wbr/>", "")
        return text

    def _enrich_transit_details(self, step_obj: TripStep, step_data: dict[str, object]) -> None:
        td = step_data.get("transit_details", {})
        td_dict = td if isinstance(td, dict) else {}
        line = td_dict.get("line", {})
        line_dict = line if isinstance(line, dict) else {}
        vehicle = line_dict.get("vehicle", {})
        vehicle_dict = vehicle if isinstance(vehicle, dict) else {}
        raw_type = _safe_str(vehicle_dict.get("type", "BUS"))

        short_name = line_dict.get("short_name")
        line_name_raw = short_name if short_name is not None else line_dict.get("name", "")

        step_obj.transit_details = TripStepTransitDetails(
            line_name=_safe_str(line_name_raw),
            line_color=_safe_str(line_dict.get("color", "#0066CC")),
            line_vehicle_type=VEHICLE_TYPE_MAP.get(raw_type, raw_type),
            departure_stop=_safe_str(_safe_get(td_dict, "departure_stop", "name")),
            arrival_stop=_safe_str(_safe_get(td_dict, "arrival_stop", "name")),
            num_stops=_safe_int(td_dict.get("num_stops", 0)),
            headsign=_safe_str(td_dict.get("headsign", "")),
        )

        vehicle_name = _safe_str(vehicle_dict.get("name", "Transporte"))
        line_name = step_obj.transit_details.line_name
        headsign = step_obj.transit_details.headsign

        step_obj.instruction = f"{vehicle_name} {line_name} direção \"{headsign}\""
