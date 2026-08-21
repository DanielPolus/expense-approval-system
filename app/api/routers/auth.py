from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.core.security import create_access_token, verify_password
from app.schemas.auth import TokenResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    norm_email = user_data.email.lower()
    statement = select(User).where(User.email == norm_email)
    existing_user = db.scalar(statement)

    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    user = User(
        full_name=user_data.full_name,
        email=norm_email,
        phone=user_data.phone,
        hashed_password=hash_password(user_data.password),
        role=UserRole.EMPLOYEE
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    norm_email = form_data.username.lower()
    password = form_data.password

    statement = select(User).where(User.email == norm_email)
    user = db.scalar(statement)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

    access_token = create_access_token(user.id)

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

