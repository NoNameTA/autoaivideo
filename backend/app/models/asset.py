from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.ids import new_id
from app.models.enums import AssetKind

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.step import Step


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("asset"))
    step_id: Mapped[str] = mapped_column(ForeignKey("steps.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    kind: Mapped[AssetKind] = mapped_column(String(20), default=AssetKind.other)
    path: Mapped[str] = mapped_column(String(500))
    mime: Mapped[str | None] = mapped_column(String(120), default=None)
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    checksum: Mapped[str | None] = mapped_column(String(64), index=True, default=None)

    step: Mapped[Step] = relationship(back_populates="assets")
    job: Mapped[Job] = relationship(back_populates="assets")
