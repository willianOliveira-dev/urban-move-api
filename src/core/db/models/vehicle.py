from datetime import datetime

import uuid_utils as uuid
from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import TransportModal


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid7()),
    )

    external_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    route_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    modal: Mapped[TransportModal] = mapped_column(
        Enum(TransportModal, native_enum=False, length=20),
        nullable=False,
        index=True,
    )

    prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_accessible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    current_location: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    speed_kmh: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    heading: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    direction: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    route: Mapped["Route"] = relationship(
        "Route",
        back_populates="vehicles",
    )

    positions: Mapped[list["VehiclePosition"]] = relationship(
        "VehiclePosition",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )

    predictions: Mapped[list["StopPrediction"]] = relationship(
        "StopPrediction",
        back_populates="vehicle",
        cascade="all, delete-orphan",
    )

    ratings: Mapped[list["Rating"]] = relationship(
        "Rating",
        back_populates="vehicle",
    )

    def __repr__(self) -> str:
        return f"<Vehicle(id={self.id}, prefix={self.prefix}, modal={self.modal})>"
