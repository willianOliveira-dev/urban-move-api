from datetime import datetime

import uuid_utils as uuid
from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import TransportModal


class Route(Base):
    __tablename__ = "routes"

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

    short_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    long_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    terminal_primary: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    terminal_secondary: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    operator: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    modal: Mapped[TransportModal] = mapped_column(
        Enum(TransportModal, native_enum=False, length=20),
        nullable=False,
        index=True
    )

    color: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
        server_default="#0066CC"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    vehicles: Mapped[list["Vehicle"]] = relationship(
        "Vehicle",
        back_populates="route",
        cascade="all, delete-orphan"
    )

    trips: Mapped[list["Trip"]] = relationship(
        "Trip",
        back_populates="route",
        cascade="all, delete-orphan"
    )

    ratings: Mapped[list["Rating"]] = relationship(
        "Rating",
        back_populates="route"
    )

    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="route"
    )

    favorited_by: Mapped[list["FavoriteRoute"]] = relationship(
        "FavoriteRoute",
        back_populates="route",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Route(id={self.id}, short_name={self.short_name}, modal={self.modal})>"
