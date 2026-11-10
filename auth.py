import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "chave-de-desenvolvimento-troque-em-producao")
ALGORITHM = "HS256"
EXPIRA_MINUTOS = 30

# pbkdf2_sha256 é puro Python no Passlib: sem a incompatibilidade passlib x bcrypt>=4
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(tags=["Autenticação"])
DB = Annotated[Session, Depends(get_db)]


class UsuarioIn(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)


class Usuario(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def criar_token(email: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=EXPIRA_MINUTOS)
    return jwt.encode({"sub": email, "exp": expira}, SECRET_KEY, algorithm=ALGORITHM)


def usuario_atual(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> models.Usuario:
    """Dependência que exige um JWT válido no header `Authorization: Bearer <token>`."""
    erro = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        email = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub")
    except jwt.InvalidTokenError:
        raise erro
    usuario = db.scalar(select(models.Usuario).where(models.Usuario.email == email))
    if usuario is None:
        raise erro
    return usuario


@router.post("/usuarios", response_model=Usuario, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: UsuarioIn, db: DB):
    if db.scalar(select(models.Usuario).where(models.Usuario.email == dados.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    usuario = models.Usuario(email=dados.email, senha_hash=pwd_context.hash(dados.senha))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/token", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    """Login OAuth2: o campo `username` recebe o e-mail."""
    usuario = db.scalar(select(models.Usuario).where(models.Usuario.email == form.username))
    if usuario is None or not pwd_context.verify(form.password, usuario.senha_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=criar_token(usuario.email))
