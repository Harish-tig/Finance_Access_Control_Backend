from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.dashboard import CategoryTotal, MonthlyTrend, DashboardSummary
from app.schemas.financial_record import RecordResponse


def _active(db: Session):
    return db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)  # noqa: E712


def get_total_income(db: Session) -> float:
    result = (
        _active(db)
        .filter(FinancialRecord.type == RecordType.INCOME)
        .with_entities(func.coalesce(func.sum(FinancialRecord.amount), 0.0))
        .scalar()
    )
    return float(result)


def get_total_expenses(db: Session) -> float:
    result = (
        _active(db)
        .filter(FinancialRecord.type == RecordType.EXPENSE)
        .with_entities(func.coalesce(func.sum(FinancialRecord.amount), 0.0))
        .scalar()
    )
    return float(result)


def get_category_totals(db: Session) -> List[CategoryTotal]:
    rows = (
        _active(db)
        .with_entities(
            FinancialRecord.category,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
        .all()
    )
    return [CategoryTotal(category=row.category, total=float(row.total)) for row in rows]


def get_recent_transactions(db: Session, limit: int = 10) -> List[RecordResponse]:
    records = (
        _active(db)
        .order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .limit(limit)
        .all()
    )
    return [RecordResponse.model_validate(r) for r in records]


def get_monthly_trends(db: Session, months: int = 12) -> List[MonthlyTrend]:
    """SQLite uses strftime for date extraction."""
    rows = (
        _active(db)
        .with_entities(
            func.strftime("%Y", FinancialRecord.date).label("year"),
            func.strftime("%m", FinancialRecord.date).label("month"),
            FinancialRecord.type,
            func.sum(FinancialRecord.amount).label("total"),
        )
        .group_by("year", "month", FinancialRecord.type)
        .order_by("year", "month")
        .all()
    )

    trend_map: dict[tuple, dict] = {}
    for row in rows:
        key = (int(row.year), int(row.month))
        if key not in trend_map:
            trend_map[key] = {"income": 0.0, "expense": 0.0}
        if row.type == RecordType.INCOME:
            trend_map[key]["income"] = float(row.total)
        else:
            trend_map[key]["expense"] = float(row.total)

    trends = []
    for (year, month), totals in sorted(trend_map.items())[-months:]:
        trends.append(
            MonthlyTrend(
                year=year,
                month=month,
                income=totals["income"],
                expense=totals["expense"],
                net=totals["income"] - totals["expense"],
            )
        )
    return trends


def get_dashboard_summary(db: Session) -> DashboardSummary:
    income = get_total_income(db)
    expenses = get_total_expenses(db)
    return DashboardSummary(
        total_income=income,
        total_expenses=expenses,
        net_balance=income - expenses,
        category_totals=get_category_totals(db),
        recent_transactions=get_recent_transactions(db),
    )
