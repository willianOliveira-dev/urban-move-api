from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.core.db.models.route import TransportModal

class StopResponse(BaseModel):
    id: str = Field(..., description="UUID of the stop")
    external_id: str = Field(..., description="External reference ID")
    name: str = Field(..., description="Stop name")
    modal: TransportModal = Field(..., description="Transport modality")
    has_shelter: bool | None = Field(None, description="Stop has shelter")
    is_accessible: bool = Field(..., description="Stop is accessible")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
