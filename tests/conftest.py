"""
Shared pytest fixtures for MinorSafe test suite.

Provides reusable Session, ClassificationResult, and mock API objects
used across validation, unit, deliverable, and integration tests.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# NOTE: These fixtures import from src/ models. If the models module has not
# yet been implemented, the import will fail and all tests will be collected
# with an error. Update the import paths once src/models.py exists.
# ---------------------------------------------------------------------------

# Lazy import guard — comment out when src/models.py is implemented
# from src.models import Session, Turn, ClassificationResult, ResponsePayload, EscalationRecord


# === Fixtures ===

@pytest.fixture
def fresh_session():
    """
    A brand-new Session for a minor user with no turns and Green risk.

    Relates to: MOD-001, VC-004
    """
    # TODO: Replace dict with Session dataclass once src/models.py exists
    return {
        "session_id": "test-session-001",
        "user_age_group": "minor",
        "risk_level": "Green",
        "cumulative_risk_score": 0.0,
        "turns": [],
        "created_at": datetime(2026, 6, 13, 12, 0, 0, tzinfo=timezone.utc),
        "escalated": False,
    }


@pytest.fixture
def sample_classification_result():
    """
    A ClassificationResult for a Yellow-risk criminal_liability message.

    Relates to: MOD-002, VC-001
    """
    # TODO: Replace dict with ClassificationResult dataclass once src/models.py exists
    return {
        "harm_category": "criminal_liability",
        "risk_level": "Yellow",
        "turn_risk_score": 0.4,
        "reasoning": "Message inquires about obtaining illegal goods without explicit intent.",
        "safe_redirect": "If you have legal questions, speaking with a trusted adult or counsellor can help.",
    }


@pytest.fixture
def red_session():
    """
    A Session that has reached Red risk with 3 turns but has not yet been escalated.

    Relates to: MOD-001, MOD-005, VC-002, VC-004
    """
    turns = [
        {
            "turn_id": i + 1,
            "user_message": f"Turn {i + 1} message",
            "classification": {
                "harm_category": "self_harm",
                "risk_level": "Orange" if i < 2 else "Red",
                "turn_risk_score": 0.6 + (i * 0.1),
                "reasoning": "Escalating distress signal.",
                "safe_redirect": "Please reach out to a crisis line.",
            },
            "timestamp": datetime(2026, 6, 13, 12, i, 0, tzinfo=timezone.utc),
        }
        for i in range(3)
    ]
    return {
        "session_id": "test-session-red-001",
        "user_age_group": "minor",
        "risk_level": "Red",
        "cumulative_risk_score": 0.85,
        "turns": turns,
        "created_at": datetime(2026, 6, 13, 12, 0, 0, tzinfo=timezone.utc),
        "escalated": False,
    }


@pytest.fixture
def mock_claude_client():
    """
    A MagicMock standing in for the Anthropic Claude API client.

    Returns a structured mock response that src/harm_classifier.py can parse.
    Relates to: MOD-002, DEL-001
    """
    client = MagicMock()

    # Simulate a minimal Claude API messages.create response
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
