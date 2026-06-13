from src import session_manager
from src.models import ClassificationResult, Session


def compute_turn_score(turn_index: int, turn_risk_score: float) -> float:
    return (turn_index + 1) * turn_risk_score


def compute_risk_level(cumulative_score: float) -> str:
    if cumulative_score >= 0.80:
        return "Red"
    if cumulative_score >= 0.55:
        return "Orange"
    if cumulative_score >= 0.30:
        return "Yellow"
    return "Green"


def _compute_cumulative(session: Session) -> float:
    n = len(session.turns)
    if n == 0:
        return 0.0
    weighted_sum = sum(
        compute_turn_score(i, turn.classification.turn_risk_score)
        for i, turn in enumerate(session.turns)
    )
    return min(weighted_sum / (n * (n + 1) / 2), 1.0)


def update(session: Session, result: ClassificationResult) -> Session:
    cumulative = _compute_cumulative(session)
    risk_level = compute_risk_level(cumulative)
    if result.risk_level == "Red":
        risk_level = "Red"
    return session_manager.update_risk(session, risk_level, cumulative)
