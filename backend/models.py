from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str] = mapped_column(String(50), nullable=False)
    lang: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    report_md: Mapped[str] = mapped_column(Text, nullable=False)
    ai_md: Mapped[str] = mapped_column(Text, nullable=False, default="")

    storage_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
