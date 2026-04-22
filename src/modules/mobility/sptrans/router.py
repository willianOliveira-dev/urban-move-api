import logging

from fastapi import APIRouter, Depends

from src.modules.mobility.sptrans.controller import SPTransController
from src.modules.mobility.sptrans.service import SPTransClient

router = APIRouter(prefix="/sptrans", tags=["SPTrans"])

_sptrans_client = SPTransClient()

def get_sptrans_controller() -> SPTransController:
    return SPTransController(_sptrans_client)

@router.get("/health/sptrans")
async def health_check_sptrans(
    controller: SPTransController = Depends(get_sptrans_controller)
) -> dict[str, object]:
    return await controller.check_health()
