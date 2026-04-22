import logging

from fastapi import HTTPException

from src.modules.mobility.sptrans.service import SPTransAuthError, SPTransClient

logger = logging.getLogger("urbanmove.mobility.sptrans")

class SPTransController:
    def __init__(self, service: SPTransClient) -> None:
        self.service = service

    async def check_health(self) -> dict[str, object]:
        try:
            is_auth = await self.service.authenticate()
            if is_auth:
                return {"status": "ok", "api": "Olho Vivo SPTrans v2.1", "authenticated": True}
            raise HTTPException(status_code=401, detail="SPTrans rejeitou as credenciais")
        except SPTransAuthError as e:
            logger.error("Falha auth SPTrans: %s", e)
            raise HTTPException(status_code=502, detail=f"Erro de conexão com gateway SPTrans: {e}")
