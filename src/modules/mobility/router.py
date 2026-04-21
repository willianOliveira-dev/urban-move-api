import logging

from fastapi import APIRouter, HTTPException

from src.modules.mobility.services.sptrans import SPTransAuthError, SPTransClient

router = APIRouter(prefix="/mobility", tags=["Mobility"])
logger = logging.getLogger("urbanmove.mobility")

_sptrans_client = SPTransClient()


@router.get("/health/sptrans")
async def health_check_sptrans() -> dict[str, object]:
    try:
        is_auth = await _sptrans_client.authenticate()
        if is_auth:
            return {"status": "ok", "api": "Olho Vivo SPTrans v2.1", "authenticated": True}

        raise HTTPException(status_code=401, detail="SPTrans rejeitou as credenciais")

    except SPTransAuthError as e:
        logger.error("Falha auth SPTrans: %s", e)
        raise HTTPException(status_code=502, detail=f"Erro de conexão com gateway SPTrans: {e}")
