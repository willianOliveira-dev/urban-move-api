from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.core.db.models.route import TransportModal

class RouteResponse(BaseModel):
    id: str = Field(..., description="UUID of the route")
    external_id: int = Field(..., description="SPTrans Line Code (cl)")
    name: str = Field(..., description="Route name/letreiro")
    modal: TransportModal = Field(..., description="Transport modality")
    color: str = Field(..., description="Route color")
    operator: str | None = Field(None, description="Operating company")
    is_active: bool = Field(..., description="If the route is active")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
