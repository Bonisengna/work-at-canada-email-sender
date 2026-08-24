from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import AuthResponse, UserCredentials

class AuthService:
    """Authentication rules live here; routers only translate HTTP intent."""
    @staticmethod
    def register(db: Session, credentials: UserCredentials) -> AuthResponse:
        email = credentials.email.lower()
        if db.scalar(select(User).where(User.email == email)):
            raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
        user = User(email=email, password_hash=hash_password(credentials.password))
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="E-mail já cadastrado.")
        db.refresh(user)
        token, expires_in = create_access_token(str(user.id))
        return AuthResponse(access_token=token, expires_in=expires_in, user=user)

    @staticmethod
    def login(db: Session, credentials: UserCredentials) -> AuthResponse:
        user = db.scalar(select(User).where(User.email == credentials.email.lower()))
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos.")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Usuário inativo.")
        token, expires_in = create_access_token(str(user.id))
        return AuthResponse(access_token=token, expires_in=expires_in, user=user)

