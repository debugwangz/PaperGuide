import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class DailyEntry(Base):
    __tablename__ = "daily_entry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    entry_text: Mapped[str] = mapped_column(Text, nullable=False)
    enrich_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrich_version: Mapped[str] = mapped_column(String(20), default="v1")
    user_id: Mapped[str] = mapped_column(String(50), default="local")


class ReviewReport(Base):
    __tablename__ = "review_report"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # week|month|quarter|year
    period_key: Mapped[str] = mapped_column(String(20), nullable=False)   # 2026-W06, 2026-02, etc.
    time_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    time_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    report_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    report_version: Mapped[str] = mapped_column(String(20), default="v1")
    user_id: Mapped[str] = mapped_column(String(50), default="local")
