import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.models import EscalationRecord, Session


def build_record(session: Session) -> EscalationRecord:
    detected = list({
        turn.classification.harm_category
        for turn in session.turns
        if turn.classification.harm_category != "none"
    })
    return EscalationRecord(
        record_id=str(uuid.uuid4()),
        session_id=session.session_id,
        timestamp=datetime.now(timezone.utc),
        trigger_turn_id=len(session.turns) - 1,
        final_risk_score=session.cumulative_risk_score,
        turn_count=len(session.turns),
        harm_categories_detected=detected,
    )


def trigger(session: Session) -> Optional[EscalationRecord]:
    if session.escalated:
        return None
    return build_record(session)


def log_record(record: EscalationRecord, log_path) -> None:
    data = {
        "record_id": record.record_id,
        "session_id": record.session_id,
        "timestamp": record.timestamp.isoformat(),
        "trigger_turn_id": record.trigger_turn_id,
        "final_risk_score": record.final_risk_score,
        "turn_count": record.turn_count,
        "harm_categories_detected": record.harm_categories_detected,
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(data) + "\n")
