from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, RefreshRequest, TokenResponse
from app.services.user_service import authenticate_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.utils.rate_limiter import rate_limit

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit)])
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email + password. Returns access + refresh tokens."""
    user = authenticate_user(db, data.email, data.password)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(rate_limit)])
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new token pair."""
    payload = decode_token(data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user = db.get(User, int(payload["sub"]))

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )
