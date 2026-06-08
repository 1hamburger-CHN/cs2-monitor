"""Fernet symmetric encryption for Steam API Key and Server酱 SendKey."""
from cryptography.fernet import Fernet
from app.config import settings


def get_fernet() -> Fernet:
    if not settings.encryption_key:
        raise ValueError(
            "ENCRYPTION_KEY not set. Generate with: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(settings.encryption_key.encode())


def encrypt_value(value: str) -> str:
    if not value:
        return value
    return get_fernet().encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    if not encrypted:
        return encrypted
    return get_fernet().decrypt(encrypted.encode()).decode()
