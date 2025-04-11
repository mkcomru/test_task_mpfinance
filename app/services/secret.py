import datetime
from typing import Optional, Dict, Any

from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session

from app.models.logs import ActionType
from app.models.secret import Secret
from app.schemas.secret import SecretCreate, SecretResponse, SecretRead, SecretDelete
from app.services import crypto, cache, logger

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def create_secret(
    db: Session,
    secret_data: SecretCreate,
    request: Optional[Request] = None
) -> SecretResponse:
    secret_key = crypto.generate_secret_key()
    
    log.info(f"Создаем секрет с ключом: {secret_key}")
    
    encrypted_data = crypto.encrypt_data(secret_data.secret, secret_data.passphrase)
    
    passphrase_hash = None
    if secret_data.passphrase:
        passphrase_hash = crypto.hash_passphrase(secret_data.passphrase)
    
    expires_at = None
    if secret_data.ttl_seconds:
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=secret_data.ttl_seconds)
        log.info(f"Установлен срок истечения: {expires_at.isoformat()}")
    else:
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
        log.info(f"Установлен срок истечения по умолчанию: {expires_at.isoformat()}")
    
    secret = Secret(
        secret_key=secret_key,
        encrypted_data=encrypted_data,
        passphrase_hash=passphrase_hash,
        expires_at=expires_at
    )
    
    db.add(secret)
    db.commit()
    db.refresh(secret)
    
    cache_data = {
        "encrypted_data": encrypted_data,
        "passphrase_hash": passphrase_hash,
        "is_accessed": False,
        "is_deleted": False,
        "expires_at": expires_at.isoformat() if expires_at else None
    }
    
    ttl_seconds = secret_data.ttl_seconds or 86400
    cache.set_cache(secret_key, cache_data, ttl_seconds)
    
    log.info(f"Секрет сохранен в кеше и БД: {secret_key}")
    
    logger.log_action(
        db,
        secret_key,
        ActionType.CREATE,
        request,
        {"ttl_seconds": ttl_seconds, "with_passphrase": bool(secret_data.passphrase)}
    )
    
    return SecretResponse(secret_key=secret_key)


def get_secret(
    db: Session,
    secret_key: str,
    request: Optional[Request] = None
) -> SecretRead:
    log.info(f"Запрошен секрет с ключом: {secret_key}")
    
    cached_secret = cache.get_cache(secret_key)
    log.info(f"Проверка кеша для {secret_key}: {'найден' if cached_secret else 'не найден'}")
    
    if cached_secret:
        if cached_secret.get("is_accessed", False):
            log.warning(f"Секрет {secret_key} уже был получен ранее")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret has already been accessed"
            )
        
        if cached_secret.get("is_deleted", False):
            log.warning(f"Секрет {secret_key} был удален")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret has been deleted"
            )
        
        expires_at = cached_secret.get("expires_at")
        if expires_at:
            expires_dt = datetime.datetime.fromisoformat(expires_at)
            if datetime.datetime.now(datetime.timezone.utc) >= expires_dt:
                log.warning(f"Срок действия секрета {secret_key} истек")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Secret has expired"
                )
        
        encrypted_data = cached_secret.get("encrypted_data")
        try:
            decrypted_data = crypto.decrypt_data(encrypted_data)
            log.info(f"Секрет {secret_key} успешно расшифрован")
        except Exception as e:
            log.error(f"Ошибка при расшифровке секрета {secret_key}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error decrypting secret"
            )
        
        cached_secret["is_accessed"] = True
        cache.set_cache(secret_key, cached_secret)
        log.info(f"Кеш обновлен, секрет {secret_key} помечен как прочитанный")
        
        secret = db.query(Secret).filter(Secret.secret_key == secret_key).first()
        if secret:
            secret.is_accessed = True
            db.commit()
            log.info(f"БД обновлена, секрет {secret_key} помечен как прочитанный")
        
        logger.log_action(db, secret_key, ActionType.READ, request)
        
        return SecretRead(secret=decrypted_data)
    
    log.info(f"Секрет {secret_key} не найден в кеше, ищем в БД")
    secret = db.query(Secret).filter(Secret.secret_key == secret_key).first()
    
    if not secret:
        log.warning(f"Секрет {secret_key} не найден в БД")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )
        
    if secret.is_accessed:
        log.warning(f"Секрет {secret_key} уже был получен ранее (из БД)")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret has already been accessed"
        )
        
    if secret.is_deleted:
        log.warning(f"Секрет {secret_key} был удален (из БД)")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret has been deleted"
        )
        
    if secret.is_expired():
        log.warning(f"Срок действия секрета {secret_key} истек (из БД)")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret has expired"
        )
    
    try:
        decrypted_data = crypto.decrypt_data(secret.encrypted_data)
        log.info(f"Секрет {secret_key} успешно расшифрован (из БД)")
    except Exception as e:
        log.error(f"Ошибка при расшифровке секрета {secret_key} (из БД): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error decrypting secret"
        )
    
    secret.is_accessed = True
    db.commit()
    log.info(f"БД обновлена, секрет {secret_key} помечен как прочитанный")
    
    logger.log_action(db, secret_key, ActionType.READ, request)
    
    return SecretRead(secret=decrypted_data)


def delete_secret(
    db: Session,
    secret_key: str,
    passphrase: Optional[str] = None,
    request: Optional[Request] = None
) -> SecretDelete:
    cached_secret = cache.get_cache(secret_key)
    
    if cached_secret:
        if cached_secret.get("passphrase_hash") and not passphrase:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Passphrase required to delete this secret"
            )
        
        if cached_secret.get("passphrase_hash") and passphrase:
            if not crypto.verify_passphrase(passphrase, cached_secret["passphrase_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid passphrase"
                )
        
        cached_secret["is_deleted"] = True
        cache.set_cache(secret_key, cached_secret)
    
    secret = db.query(Secret).filter(Secret.secret_key == secret_key).first()
    
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )
    
    if secret.passphrase_hash and not passphrase:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Passphrase required to delete this secret"
        )
    
    if secret.passphrase_hash and passphrase:
        if not crypto.verify_passphrase(passphrase, secret.passphrase_hash):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid passphrase"
            )
    
    secret.is_deleted = True
    db.commit()
    
    logger.log_action(db, secret_key, ActionType.DELETE, request)
    
    return SecretDelete() 