"""
Shared pytest fixtures for MinorSafe test suite.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.models import ClassificationResult, EscalationRecord, ResponsePayload, Session, Turn


@pytest.fixture
def fresh_session():
    return Session(
        session_id="test-session-001",
        user_age_group="minor",
        risk_level="Green",
        cumulative_risk_score=0.0,
        turns=[],
        created_at=datetime(2026, 6, 13, 12, 0, 0, tzinfo=timezone.utc),
        escalated=False,
    )


@pytest.fixture
def sample_classification_result():
    return ClassificationResult(
        harm_category="criminal_liability",
        risk_level="Yellow",
        turn_risk_score=0.4,
        safe_redirect="If you have legal questions, speaking with a trusted adult or counsellor can help.",
        reasoning="Message inquires about obtaining illegal goods without explicit intent.",
    )


@pytest.fixture
def red_session():
    turns = [
        Turn(
            turn_id=i,
            user_message=f"Turn {i + 1} message",
            classification=ClassificationResult(
                harm_category="self_harm",
                risk_level="Orange" if i < 2 else "Red",
                turn_risk_score=0.6 + (i * 0.1),
                safe_redirect="Please reach out to a crisis line.",
                reasoning="Escalating distress signal.",
            ),
            timestamp=datetime(2026, 6, 13, 12, i, 0, tzinfo=timezone.utc),
        )
        for i in range(3)
    ]
    return Session(
        session_id="test-session-red-001",
        user_age_group="minor",
        risk_level="Red",
        cumulative_risk_score=0.85,
        turns=turns,
        created_at=datetime(2026, 6, 13, 12, 0, 0, tzinfo=timezone.utc),
        escalated=False,
    )


@pytest.fixture
def mock_claude_client():
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [
        MagicMock(
            text='{"harm_category": "criminal_liability", "risk_level": "Yellow", '
                 '"turn_risk_score": 0.4, "reasoning": "Mock reasoning.", '
                 '"safe_redirect": "Mock redirect."}'
        )
    ]
    client.messages.create.return_value = mock_response
    return client
