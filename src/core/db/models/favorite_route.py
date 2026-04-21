from datetime import datetime

import uuid_utils as uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class FavoriteRoute(Base):
    __tablename__ = "favorite_routes"

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

    route_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    nickname: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    notify_delays: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true"
    )

    notify_changes: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true"
    )

    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    route: Mapped["Route"] = relationship(
        "Route",
        back_populates="favorited_by"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "route_id",
            name="uq_user_route_favorite"
        ),
        Index(
            "ix_favorite_routes_user_order",
            "user_id",
            "display_order"
        ),
    )

    def __repr__(self) -> str:
        return f"<FavoriteRoute(id={self.id}, user_id={self.user_id}, route_id={self.route_id})>"
