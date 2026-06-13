from datetime import datetime, timezone
from typing import Optional
import uuid

from src.models import Session, Turn

_store: dict = {}


def create_session(user_age_group: str) -> Session:
    session = Session(
        session_id=str(uuid.uuid4()),
        user_age_group=user_age_group,
        created_at=datetime.now(timezone.utc),
    )
    _store[session.session_id] = session
    return session


def add_turn(session: Session, turn: Turn) -> Session:
    session.turns.append(turn)
    _store[session.session_id] = session
    return session


def get_session(session_id: str) -> Optional[Session]:
    return _store.get(session_id)


def update_risk(session: Session, risk_level: str, cumulative_score: float) -> Session:
    session.risk_level = risk_level
    session.cumulative_risk_score = cumulative_score
    _store[session.session_id] = session
    return session


def mark_escalated(session: Session) -> Session:
    session.escalated = True
    _store[session.session_id] = session
    return session
