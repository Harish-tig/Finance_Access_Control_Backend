from typing import List
from pydantic import BaseModel
from app.schemas.financial_record import RecordResponse


class CategoryTotal(BaseModel):
    category: str
    total: float


class MonthlyTrend(BaseModel):
    year: int
    month: int
    income: float
    expense: float
    net: float


class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    category_totals: List[CategoryTotal]
    recent_transactions: List[RecordResponse]
