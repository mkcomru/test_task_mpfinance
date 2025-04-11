import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base, TimeStampMixin


class Secret(Base, TimeStampMixin):
    __tablename__ = "secrets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    secret_key = Column(String, unique=True, index=True, nullable=False)
    encrypted_data = Column(Text, nullable=False)
    passphrase_hash = Column(String, nullable=True)
    is_accessed = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.datetime.now(self.expires_at.tzinfo) >= self.expires_at 