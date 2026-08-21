import jwt
from collections.abc import Generator
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from app.db.session import SessionLocal
from app.core.config import settings
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    return user

def require_manager(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")

    return current_user

def require_accountant(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ACCOUNTANT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accountant access required")

    return current_user

