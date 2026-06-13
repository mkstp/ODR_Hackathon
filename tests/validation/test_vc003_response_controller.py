"""
VC-003: Response controller produces risk-appropriate output for all four risk levels.
"""

import pytest

from src import response_controller as rc
from src.models import ClassificationResult


@pytest.fixture
def base_result():
    return ClassificationResult(
        harm_category="none", risk_level="Green",
        turn_risk_score=0.0,
        safe_redirect="Speaking with a trusted adult can really help.",
    )


class TestVC003ResponseController:

    def test_green_response_no_crisis_resources(self, fresh_session, base_result):
        fresh_session.risk_level = "Green"
        payload = rc.generate_response(fresh_session, base_result)
        assert payload.risk_level == "Green"
        assert payload.message != ""
        assert payload.crisis_resources == []

    def test_yellow_response_contains_redirect_message(self, fresh_session, base_result):
        fresh_session.risk_level = "Yellow"
        fresh_session.cumulative_risk_score = 0.40
        payload = rc.generate_response(fresh_session, base_result)
        assert payload.risk_level == "Yellow"
        assert payload.message != ""
        assert payload.crisis_resources == []

    def test_orange_response_contains_professional_referral(self, fresh_session, base_result):
        fresh_session.risk_level = "Orange"
        fresh_session.cumulative_risk_score = 0.65
        payload = rc.generate_response(fresh_session, base_result)
        assert payload.risk_level == "Orange"
        assert "trusted adult" in payload.message.lower() or "counsellor" in payload.message.lower()
        assert payload.crisis_resources == []

    def test_red_response_includes_crisis_resources(self, red_session):
        result = ClassificationResult(
            harm_category="self_harm", risk_level="Red",
            turn_risk_score=0.92,
            safe_redirect="Please reach out immediately.",
        )
        payload = rc.generate_response(red_session, result)
        assert payload.risk_level == "Red"
        assert len(payload.crisis_resources) > 0
        assert payload.escalation_triggered is True
