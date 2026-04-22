import logging

import httpx

from src.core.config.env import env

logger = logging.getLogger("urbanmove.sptrans")


class SPTransClientError(Exception):
    pass


class SPTransAuthError(SPTransClientError):
    pass


class SPTransClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=env.SPTRANS_API_URL,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
        self._is_authenticated = False

    async def authenticate(self) -> bool:
        try:
            response = await self._client.post(
                "/Login/Autenticar",
                params={"token": env.SPTRANS_API_TOKEN},
            )
            response.raise_for_status()

            result = response.json()
            self._is_authenticated = result is True

            if self._is_authenticated:
                logger.info("Autenticado com sucesso na SPTrans")
            else:
                logger.warning("SPTrans recusou o token de autenticação")

            return self._is_authenticated

        except httpx.HTTPError as e:
            logger.error("Falha de rede ao autenticar na SPTrans: %s", e)
            raise SPTransAuthError(f"Falha de comunicação: {e}")

    async def _ensure_auth(self) -> None:
        if not self._is_authenticated:
            await self.authenticate()

    async def get_vehicle_positions(self, route_code: int) -> dict[str, object]:
        await self._ensure_auth()
        try:
            response = await self._client.get(
                "/Posicao/Linha",
                params={"codigoLinha": route_code},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self._is_authenticated = False
                await self._ensure_auth()
                return await self.get_vehicle_positions(route_code)
            raise SPTransClientError(f"Erro ao buscar posições: {e}")
        except httpx.HTTPError as e:
            raise SPTransClientError(f"Erro ao buscar posições: {e}")

    async def get_arrival_prediction(self, stop_code: int, route_code: int) -> dict[str, object]:
        await self._ensure_auth()
        try:
            response = await self._client.get(
                "/Previsao",
                params={"codigoParada": stop_code, "codigoLinha": route_code},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self._is_authenticated = False
                await self._ensure_auth()
                return await self.get_arrival_prediction(stop_code, route_code)
            raise SPTransClientError(f"Erro ao buscar previsão: {e}")
        except httpx.HTTPError as e:
            raise SPTransClientError(f"Erro ao buscar previsão: {e}")

    async def search_routes(self, search_term: str) -> list[dict[str, object]]:
        await self._ensure_auth()
        try:
            response = await self._client.get(
                "/Linha/Buscar",
                params={"termosBusca": search_term},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise SPTransClientError(f"Erro ao buscar linhas: {e}")

    async def search_stops(self, search_term: str) -> list[dict[str, object]]:
        await self._ensure_auth()
        try:
            response = await self._client.get(
                "/Parada/Buscar",
                params={"termosBusca": search_term},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise SPTransClientError(f"Erro ao buscar paradas: {e}")

    async def get_stop_predictions(self, external_stop_id: str) -> dict[str, object]:
        """Busca previsões de chegada para uma parada específica."""
        await self._ensure_auth()
        try:
            response = await self._client.get(
                "/Previsao/Parada",
                params={"codigoParada": external_stop_id},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                self._is_authenticated = False
                await self._ensure_auth()
                return await self.get_stop_predictions(external_stop_id)
            raise SPTransClientError(f"Erro ao buscar previsões: {e}")
        except httpx.HTTPError as e:
            raise SPTransClientError(f"Erro ao buscar previsões: {e}")

    async def close(self) -> None:
        await self._client.aclose()
        self._client = httpx.AsyncClient(
            base_url=env.SPTRANS_API_URL,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
        self._is_authenticated = False
