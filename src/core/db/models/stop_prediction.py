from datetime import datetime

import uuid_utils as uuid
from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class StopPrediction(Base):
    __tablename__ = "stop_predictions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid7())
    )

    stop_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("stops.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    route_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    predicted_eta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    distance_meters: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    stop: Mapped["Stop"] = relationship(
        "Stop",
        back_populates="predictions"
    )

    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        back_populates="predictions"
    )

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def __repr__(self) -> str:
        return f"<StopPrediction(id={self.id}, stop_id={self.stop_id}, eta={self.predicted_eta})>"
