from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ClassificationResult:
    harm_category: str
    risk_level: str
    turn_risk_score: float
    safe_redirect: str
    reasoning: Optional[str] = None


@dataclass
class Turn:
    turn_id: int
    user_message: str
    classification: ClassificationResult
    timestamp: datetime


@dataclass
class Session:
    session_id: str
    user_age_group: str
    risk_level: str = "Green"
    cumulative_risk_score: float = 0.0
    turns: list = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    escalated: bool = False


@dataclass
class ResponsePayload:
    risk_level: str
    message: str
    crisis_resources: list = field(default_factory=list)
    escalation_triggered: bool = False


@dataclass
class EscalationRecord:
    record_id: str
    session_id: str
    timestamp: datetime
    trigger_turn_id: int
    final_risk_score: float
    turn_count: int
    harm_categories_detected: list
