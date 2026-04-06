from sqlalchemy.orm import Session

from app.db.session import engine, Base
from app.models.user import User, UserRole
from app.models.financial_record import FinancialRecord  # noqa: F401
from app.core.security import hash_password
from app.core.config import get_settings


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    settings = get_settings()
    from app.db.session import SessionLocal
    db: Session = SessionLocal()
    try:
        if not db.query(User).first():
            admin = User(
                email=settings.admin_email,
                full_name="System Admin",
                hashed_password=hash_password(settings.admin_password),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"✅ Default admin created: {settings.admin_email}")
    finally:
        db.close()
