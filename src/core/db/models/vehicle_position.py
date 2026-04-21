from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class VehiclePosition(Base):
    __tablename__ = "vehicle_positions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    location: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False
    )

    speed_kmh: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )

    heading: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    vehicle: Mapped["Vehicle"] = relationship(
        "Vehicle",
        back_populates="positions"
    )

    __table_args__ = (
        Index(
            "ix_vehicle_positions_vehicle_recorded",
            "vehicle_id",
            "recorded_at",
            postgresql_ops={"recorded_at": "DESC"}
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<VehiclePosition(id={self.id},"
            f" vehicle_id={self.vehicle_id}, recorded_at={self.recorded_at})>"
        )
