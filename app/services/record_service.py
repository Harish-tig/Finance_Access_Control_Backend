from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.financial_record import RecordCreate, RecordUpdate


def _active_records(db: Session):
    return db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)  # noqa: E712


def create_record(db: Session, data: RecordCreate) -> FinancialRecord:
    record = FinancialRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_record(db: Session, record_id: int) -> FinancialRecord:
    record = _active_records(db).filter(FinancialRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    return record


def list_records(
    db: Session,
    record_type: Optional[RecordType] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[FinancialRecord]:
    query = _active_records(db)

    if record_type:
        query = query.filter(FinancialRecord.type == record_type)
    if category:
        query = query.filter(FinancialRecord.category == category.lower())
    if date_from:
        query = query.filter(FinancialRecord.date >= date_from)
    if date_to:
        query = query.filter(FinancialRecord.date <= date_to)

    return query.order_by(FinancialRecord.date.desc()).offset(offset).limit(limit).all()


def update_record(db: Session, record_id: int, data: RecordUpdate) -> FinancialRecord:
    record = get_record(db, record_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


def soft_delete_record(db: Session, record_id: int) -> None:
    record = get_record(db, record_id)
    record.is_deleted = True
    db.commit()
