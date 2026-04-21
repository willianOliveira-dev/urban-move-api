from datetime import datetime

import uuid_utils as uuid
from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import ReportCategory, ReportStatus


class Report(Base):
    __tablename__ = "reports"

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

    stop_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("stops.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    category: Mapped[ReportCategory] = mapped_column(
        Enum(ReportCategory, native_enum=False, length=50),
        nullable=False,
        index=True
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    location: Mapped[str | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True
    )

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, native_enum=False, length=20),
        nullable=False,
        server_default=ReportStatus.PENDING.value,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    route: Mapped["Route | None"] = relationship(
        "Route",
        back_populates="reports"
    )

    stop: Mapped["Stop | None"] = relationship(
        "Stop",
        back_populates="reports"
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, category={self.category}, status={self.status})>"
