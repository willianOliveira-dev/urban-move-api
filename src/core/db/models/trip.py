from datetime import datetime

import uuid_utils as uuid
from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import TripDirection


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid7())
    )

    external_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )

    route_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    service_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    trip_headsign: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    direction_id: Mapped[TripDirection] = mapped_column(
        Enum(TripDirection, native_enum=False),
        nullable=False,
        server_default=str(TripDirection.PRIMARY_TO_SECONDARY.value)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    route: Mapped["Route"] = relationship(
        "Route",
        back_populates="trips"
    )

    def __repr__(self) -> str:
        return (
            f"<Trip(id={self.id}, external_id={self.external_id},"
            f" headsign={self.trip_headsign})>"
        )
