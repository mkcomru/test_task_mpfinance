from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.secret import SecretCreate, SecretResponse, SecretRead, SecretDelete, PassphraseVerify
from app.services import secret as secret_service

secret_router = APIRouter()


@secret_router.post(
    "",
    response_model=SecretResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание секрета",
    description="Создает новый секрет и возвращает уникальный ключ для доступа к нему."
)
async def create_secret(
    secret_data: SecretCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    return secret_service.create_secret(db, secret_data, request)


@secret_router.get(
    "/{secret_key}",
    response_model=SecretRead,
    summary="Получение секрета",
    description="Получает секрет по ключу. Секрет становится недоступен после первого запроса."
)
async def read_secret(
    secret_key: str,
    request: Request,
    db: Session = Depends(get_db)
):
    return secret_service.get_secret(db, secret_key, request)


@secret_router.delete(
    "/{secret_key}",
    response_model=SecretDelete,
    summary="Удаление секрета",
    description="Удаляет секрет по ключу. Может потребоваться фраза-пароль, если она была указана при создании."
)
async def delete_secret(
    secret_key: str,
    request: Request,
    passphrase_data: Optional[PassphraseVerify] = Body(None),
    db: Session = Depends(get_db)
):
    passphrase_value = passphrase_data.passphrase if passphrase_data else None
    return secret_service.delete_secret(db, secret_key, passphrase_value, request) 