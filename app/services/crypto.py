import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
import logging

from app.core.config import settings

log = logging.getLogger(__name__)

def get_encryption_key():
    key_base = settings.SECRET_KEY.encode()
    key_bytes = key_base[:32].ljust(32, b'0')
    return base64.urlsafe_b64encode(key_bytes)

fernet = Fernet(get_encryption_key())

def generate_secret_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()

def hash_passphrase(passphrase: str) -> str:
    from hashlib import sha256
    salt = settings.SECRET_KEY[:16]
    return sha256((passphrase + salt).encode()).hexdigest()

def verify_passphrase(plain_passphrase: str, hashed_passphrase: str) -> bool:
    return hash_passphrase(plain_passphrase) == hashed_passphrase

def encrypt_data(data: str, passphrase: Optional[str] = None) -> str:
    try:
        encrypted_data = fernet.encrypt(data.encode())
        return encrypted_data.decode()
    except Exception as e:
        log.error(f"Ошибка шифрования: {str(e)}")
        raise

def decrypt_data(encrypted_data: str, passphrase: Optional[str] = None) -> str:
    try:
        decrypted_data = fernet.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except Exception as e:
        log.error(f"Ошибка дешифрования: {str(e)}")
        raise 