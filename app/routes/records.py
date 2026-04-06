from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.decorators import require_admin, require_viewer
from app.models.user import User
from app.models.financial_record import RecordType
from app.schemas.financial_record import RecordCreate, RecordUpdate, RecordResponse
from app.services import record_service
from app.utils.rate_limiter import rate_limit
from app.utils.redis_client import cache_delete_pattern

router = APIRouter(prefix="/records", tags=["Financial Records"], dependencies=[Depends(rate_limit)])


async def _bust_dashboard_cache():
    await cache_delete_pattern("dashboard:*")


@router.post("/", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
@require_admin
async def create_record(
    data: RecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = record_service.create_record(db, data)
    await _bust_dashboard_cache()
    return record


@router.get("/", response_model=List[RecordResponse])
@require_viewer
async def list_records(
    record_type: Optional[RecordType] = Query(None, alias="type"),
    category: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return record_service.list_records(db, record_type, category, date_from, date_to, limit, offset)


@router.get("/{record_id}", response_model=RecordResponse)
@require_viewer
async def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return record_service.get_record(db, record_id)


@router.patch("/{record_id}", response_model=RecordResponse)
@require_admin
async def update_record(
    record_id: int,
    data: RecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = record_service.update_record(db, record_id, data)
    await _bust_dashboard_cache()
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_admin
async def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record_service.soft_delete_record(db, record_id)
    await _bust_dashboard_cache()
