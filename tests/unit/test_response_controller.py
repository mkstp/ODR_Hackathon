"""
Unit tests for ResponseController (MOD-004).
"""

import pytest
from src import response_controller as rc
from src.constants import CRISIS_RESOURCES, ORANGE_RESTRICTED_PREFIX, YELLOW_WARNING_PREFIX
from src.models import ClassificationResult


@pytest.fixture
def safe_result():
    return ClassificationResult(
        harm_category="none",
        risk_level="Green",
        turn_risk_score=0.05,
        safe_redirect="Happy to help with that.",
    )


class TestGenerateResponse:

    def test_green_uses_safe_redirect_as_message(self, fresh_session, safe_result):
        fresh_session.risk_level = "Green"
        payload = rc.generate_response(fresh_session, safe_result)
        assert payload.risk_level == "Green"
        assert payload.message == safe_result.safe_redirect
        assert payload.crisis_resources == []

    def test_yellow_prefixes_message_with_warning(self, fresh_session, safe_result):
        fresh_session.risk_level = "Yellow"
        payload = rc.generate_response(fresh_session, safe_result)
        assert payload.risk_level == "Yellow"
        assert payload.message.startswith(YELLOW_WARNING_PREFIX)
        assert safe_result.safe_redirect in payload.message
        assert payload.crisis_resources == []

    def test_orange_prefixes_message_and_mentions_trusted_adult(self, fresh_session, safe_result):
        fresh_session.risk_level = "Orange"
        payload = rc.generate_response(fresh_session, safe_result)
        assert payload.risk_level == "Orange"
        assert payload.message.startswith(ORANGE_RESTRICTED_PREFIX)
        assert "trusted adult" in payload.message.lower()
        assert payload.crisis_resources == []

    def test_red_includes_crisis_resources(self, red_session):
        result = ClassificationResult(
            harm_category="self_harm", risk_level="Red",
            turn_risk_score=0.9, safe_redirect="Please reach out.",
        )
        payload = rc.generate_response(red_session, result)
        assert payload.risk_level == "Red"
        assert len(payload.crisis_resources) > 0
        assert payload.crisis_resources == CRISIS_RESOURCES

    def test_red_escalation_triggered_when_not_yet_escalated(self, red_session):
        result = ClassificationResult(
            harm_category="self_harm", risk_level="Red",
            turn_risk_score=0.9, safe_redirect="",
        )
        payload = rc.generate_response(red_session, result)
        assert payload.escalation_triggered is True

    def test_red_not_retriggered_if_already_escalated(self, red_session):
        red_session.escalated = True
        result = ClassificationResult(
            harm_category="self_harm", risk_level="Red",
            turn_risk_score=0.9, safe_redirect="",
        )
        payload = rc.generate_response(red_session, result)
        assert payload.escalation_triggered is False


class TestShouldEscalate:

    def test_true_for_red_not_escalated(self, red_session):
        assert rc.should_escalate(red_session) is True

    def test_false_when_already_escalated(self, red_session):
        red_session.escalated = True
        assert rc.should_escalate(red_session) is False

    def test_false_for_non_red_risk_levels(self, fresh_session):
        for level in ("Green", "Yellow", "Orange"):
            fresh_session.risk_level = level
            assert rc.should_escalate(fresh_session) is False
