from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import AuthResponse, UserCredentials
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
Database = Annotated[Session, Depends(get_db)]

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(credentials: UserCredentials, db: Database) -> AuthResponse:
    return AuthService.register(db, credentials)

@router.post("/login", response_model=AuthResponse)
def login(credentials: UserCredentials, db: Database) -> AuthResponse:
    return AuthService.login(db, credentials)

