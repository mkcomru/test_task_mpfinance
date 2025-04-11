from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SecretCreate(BaseModel):
    secret: str = Field(..., description="Конфиденциальные данные", min_length=1)
    passphrase: Optional[str] = Field(None, description="Фраза-пароль для дополнительной защиты")
    ttl_seconds: Optional[int] = Field(None, description="Время жизни секрета в секундах", gt=0)


class SecretResponse(BaseModel):
    secret_key: str = Field(..., description="Уникальный идентификатор секрета")


class SecretRead(BaseModel):
    secret: str = Field(..., description="Конфиденциальные данные")


class SecretDelete(BaseModel):
    status: str = Field("secret_deleted", description="Статус операции удаления")


class PassphraseVerify(BaseModel):
    passphrase: str = Field(..., description="Фраза-пароль для удаления секрета") 