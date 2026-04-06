from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.decorators import require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services import user_service
from app.utils.rate_limiter import rate_limit

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(rate_limit)])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@require_admin
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.create_user(db, data)


@router.get("/", response_model=List[UserResponse])
@require_admin
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.list_users(db)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
@require_admin
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.get_user_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
@require_admin
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return user_service.update_user(db, user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_admin
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_service.delete_user(db, user_id)
