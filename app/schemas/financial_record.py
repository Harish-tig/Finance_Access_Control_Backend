from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from app.models.financial_record import RecordType


class RecordCreate(BaseModel):
    amount: float
    type: RecordType
    category: str
    date: date
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero.")
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Category cannot be blank.")
        return v.strip().lower()


class RecordUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than zero.")
        return round(v, 2) if v else v


class RecordResponse(BaseModel):
    id: int
    amount: float
    type: RecordType
    category: str
    date: date
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RecordFilter(BaseModel):
    """Query parameters for filtering financial records."""
    type: Optional[RecordType] = None
    category: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
