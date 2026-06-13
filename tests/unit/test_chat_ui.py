"""
Unit tests for ChatUI.handle_input (MOD-006).

Tests the orchestration logic only — Streamlit rendering is not tested.
The HarmClassifier is mocked to avoid live API calls.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.models import ClassificationResult, ResponsePayload


MOCK_RESULT = ClassificationResult(
    harm_category="none",
    risk_level="Green",
    turn_risk_score=0.05,
    safe_redirect="Happy to help!",
)


class TestHandleInput:

    def test_handle_input_returns_response_payload(self, fresh_session):
        with patch("src.chat_ui._classifier") as mock_clf:
            mock_clf.classify.return_value = MOCK_RESULT
            from src.chat_ui import handle_input
            payload = handle_input("Hello", fresh_session)
        assert isinstance(payload, ResponsePayload)
        assert payload.risk_level == "Green"

    def test_handle_input_adds_turn_to_session(self, fresh_session):
        with patch("src.chat_ui._classifier") as mock_clf:
            mock_clf.classify.return_value = MOCK_RESULT
            from src.chat_ui import handle_input
            handle_input("Hello", fresh_session)
        assert len(fresh_session.turns) == 1
        assert fresh_session.turns[0].user_message == "Hello"

    def test_handle_input_calls_classifier_before_tracker(self, fresh_session):
        call_order = []
        mock_result = MOCK_RESULT

        with patch("src.chat_ui._classifier") as mock_clf, \
             patch("src.chat_ui.pattern_risk_tracker") as mock_tracker:
            mock_clf.classify.side_effect = lambda *a, **kw: (
                call_order.append("classify") or mock_result
            )
            mock_tracker.update.side_effect = lambda s, r: (
                call_order.append("update") or s
            )
            from src.chat_ui import handle_input
            handle_input("Hello", fresh_session)

        assert call_order.index("classify") < call_order.index("update")

    def test_handle_input_does_not_escalate_for_green(self, fresh_session):
        with patch("src.chat_ui._classifier") as mock_clf, \
             patch("src.chat_ui.odr_escalation_trigger") as mock_odt:
            mock_clf.classify.return_value = MOCK_RESULT
            from src.chat_ui import handle_input
            handle_input("Hello", fresh_session)
        mock_odt.log_record.assert_not_called()

    def test_handle_input_escalates_at_red(self, red_session):
        red_result = ClassificationResult(
            harm_category="self_harm", risk_level="Red",
            turn_risk_score=0.95, safe_redirect="Please reach out.",
        )
        with patch("src.chat_ui._classifier") as mock_clf:
            mock_clf.classify.return_value = red_result
            from src.chat_ui import handle_input
            payload = handle_input("I want to hurt myself", red_session)
        assert payload.escalation_triggered is True
