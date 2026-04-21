from datetime import datetime

import uuid_utils as uuid
from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import TransportModal


class Stop(Base):
    __tablename__ = "stops"

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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    modal: Mapped[TransportModal] = mapped_column(
        Enum(TransportModal, native_enum=False, length=20),
        nullable=False,
        index=True
    )

    location: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False
    )

    has_shelter: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    is_accessible: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    predictions: Mapped[list["StopPrediction"]] = relationship(
        "StopPrediction",
        back_populates="stop",
        cascade="all, delete-orphan"
    )

    ratings: Mapped[list["Rating"]] = relationship(
        "Rating",
        back_populates="stop"
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="stop"
    )

    def __repr__(self) -> str:
        return f"<Stop(id={self.id}, name={self.name}, modal={self.modal})>"
