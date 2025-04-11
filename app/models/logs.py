from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid

from app.models.base import Base, TimeStampMixin


class ActionType(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    DELETE = "delete"


class SecretLog(Base, TimeStampMixin):
    __tablename__ = "secret_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    secret_key = Column(String, index=True, nullable=False)
    action = Column(Enum(ActionType), nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    additional_data = Column(Text, nullable=True) 