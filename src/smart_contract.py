from typing import Optional

from src.models import Session

CLAUSES = {
    "CLAUSE_1": {
        "condition": "cumulative_risk_score >= 0.30",
        "action": "limit_conversation_duration",
        "description": "Yellow threshold exceeded — session time-limited.",
    },
    "CLAUSE_2": {
        "condition": "cumulative_risk_score >= 0.55",
        "action": "require_guardian_confirmation",
        "description": "Orange threshold exceeded — guardian confirmation required.",
    },
    "CLAUSE_3": {
        "condition": "cumulative_risk_score >= 0.80 or risk_level == Red",
        "action": "disable_ai_functions + trigger_odr_escalation",
        "description": "Red threshold exceeded — AI functions suspended, ODR case opened.",
    },
}


def evaluate(session: Session) -> Optional[dict]:
    """Return the highest-priority active clause for the session, or None if below CLAUSE_1."""
    if session.cumulative_risk_score >= 0.80 or session.risk_level == "Red":
        return {"key": "CLAUSE_3", **CLAUSES["CLAUSE_3"]}
    if session.cumulative_risk_score >= 0.55:
        return {"key": "CLAUSE_2", **CLAUSES["CLAUSE_2"]}
    if session.cumulative_risk_score >= 0.30:
        return {"key": "CLAUSE_1", **CLAUSES["CLAUSE_1"]}
    return None
