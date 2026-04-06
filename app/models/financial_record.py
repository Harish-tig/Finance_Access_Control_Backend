from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import String, Numeric, Date, DateTime, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.db.session import Base


class RecordType(str, enum.Enum):
    INCOME  = "income"
    EXPENSE = "expense"


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id: Mapped[int]              = mapped_column(primary_key=True, index=True)
    amount: Mapped[float]        = mapped_column(Numeric(precision=15, scale=2), nullable=False)
    type: Mapped[RecordType]     = mapped_column(SAEnum(RecordType), nullable=False, index=True)
    category: Mapped[str]        = mapped_column(String(100), nullable=False, index=True)
    date: Mapped[date]           = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Soft delete — deleted records are excluded from queries but kept in DB
    is_deleted: Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<FinancialRecord id={self.id} type={self.type} amount={self.amount}>"
