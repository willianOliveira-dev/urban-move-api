from datetime import datetime

import uuid_utils as uuid
from sqlalchemy import DateTime, Enum, ForeignKey, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import RatingCategory


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid7())
    )

    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        index=True
    )

    route_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("routes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    vehicle_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True
    )

    stop_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("stops.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False
    )

    category: Mapped[RatingCategory | None] = mapped_column(
        Enum(RatingCategory, native_enum=False, length=50),
        nullable=True
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    route: Mapped["Route | None"] = relationship(
        "Route",
        back_populates="ratings"
    )

    vehicle: Mapped["Vehicle | None"] = relationship(
        "Vehicle",
        back_populates="ratings"
    )

    stop: Mapped["Stop | None"] = relationship(
        "Stop",
        back_populates="ratings"
    )

    def __repr__(self) -> str:
        return f"<Rating(id={self.id}, score={self.score}, category={self.category})>"
