from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.decorators import require_viewer, require_analyst
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, CategoryTotal, MonthlyTrend
from app.schemas.financial_record import RecordResponse
from app.services import dashboard_service
from app.utils.rate_limiter import rate_limit
from app.utils.redis_client import cache_get, cache_set

router = APIRouter(prefix="/dashboard", tags=["Dashboard"], dependencies=[Depends(rate_limit)])

CACHE_TTL = 300


@router.get("/summary", response_model=DashboardSummary)
@require_viewer
async def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = "dashboard:summary"
    cached = await cache_get(cache_key)
    if cached:
        return DashboardSummary(**cached)

    summary = dashboard_service.get_dashboard_summary(db)
    await cache_set(cache_key, summary.model_dump(), ttl=CACHE_TTL)
    return summary


@router.get("/income", response_model=dict)
@require_analyst
async def get_total_income(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = "dashboard:total_income"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    result = {"total_income": dashboard_service.get_total_income(db)}
    await cache_set(cache_key, result, ttl=CACHE_TTL)
    return result


@router.get("/expenses", response_model=dict)
@require_analyst
async def get_total_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = "dashboard:total_expenses"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    result = {"total_expenses": dashboard_service.get_total_expenses(db)}
    await cache_set(cache_key, result, ttl=CACHE_TTL)
    return result


@router.get("/net-balance", response_model=dict)
@require_analyst
async def get_net_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = "dashboard:net_balance"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    income = dashboard_service.get_total_income(db)
    expenses = dashboard_service.get_total_expenses(db)
    result = {"total_income": income, "total_expenses": expenses, "net_balance": income - expenses}
    await cache_set(cache_key, result, ttl=CACHE_TTL)
    return result


@router.get("/categories", response_model=List[CategoryTotal])
@require_analyst
async def get_category_totals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = "dashboard:categories"
    cached = await cache_get(cache_key)
    if cached:
        return [CategoryTotal(**item) for item in cached]

    totals = dashboard_service.get_category_totals(db)
    await cache_set(cache_key, [t.model_dump() for t in totals], ttl=CACHE_TTL)
    return totals


@router.get("/recent", response_model=List[RecordResponse])
@require_viewer
async def get_recent_transactions(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return dashboard_service.get_recent_transactions(db, limit)


@router.get("/trends", response_model=List[MonthlyTrend])
@require_analyst
async def get_monthly_trends(
    months: int = Query(12, ge=1, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = f"dashboard:trends:{months}"
    cached = await cache_get(cache_key)
    if cached:
        return [MonthlyTrend(**item) for item in cached]

    trends = dashboard_service.get_monthly_trends(db, months)
    await cache_set(cache_key, [t.model_dump() for t in trends], ttl=CACHE_TTL)
    return trends
