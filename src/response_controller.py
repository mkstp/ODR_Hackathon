from src.constants import (
    CRISIS_RESOURCES,
    ORANGE_RESTRICTED_PREFIX,
    RED_REFUSAL_MESSAGE,
    YELLOW_WARNING_PREFIX,
)
from src.models import ClassificationResult, ResponsePayload, Session


def generate_response(session: Session, result: ClassificationResult) -> ResponsePayload:
    risk = session.risk_level

    if risk == "Green":
        return ResponsePayload(
            risk_level=risk,
            message=result.safe_redirect,
        )
    if risk == "Yellow":
        return ResponsePayload(
            risk_level=risk,
            message=YELLOW_WARNING_PREFIX + result.safe_redirect,
        )
    if risk == "Orange":
        return ResponsePayload(
            risk_level=risk,
            message=(
                ORANGE_RESTRICTED_PREFIX
                + result.safe_redirect
                + " Speaking with a trusted adult can really help."
            ),
        )
    # Red
    return ResponsePayload(
        risk_level=risk,
        message=RED_REFUSAL_MESSAGE,
        crisis_resources=CRISIS_RESOURCES[:],
        escalation_triggered=should_escalate(session),
    )


def should_escalate(session: Session) -> bool:
    return session.risk_level == "Red" and not session.escalated
