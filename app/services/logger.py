import json
from typing import Dict, Any, Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.logs import SecretLog, ActionType


def log_action(
    db: Session,
    secret_key: str,
    action: ActionType,
    request: Optional[Request] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> None:
    log_entry = SecretLog(
        secret_key=secret_key,
        action=action,
        additional_data=json.dumps(additional_data) if additional_data else None
    )
    
    if request:
        log_entry.ip_address = request.client.host if request.client else None
        log_entry.user_agent = request.headers.get("user-agent")
    
    db.add(log_entry)
    db.commit() 