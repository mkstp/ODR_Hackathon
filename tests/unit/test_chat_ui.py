"""
Test: Unit tests for ChatUI

Module: MOD-006
Implements: DEL-001
Purpose: Streamlit interface with risk meter. Calls pipeline modules in sequence
         when a user submits a message.

Public Interface:
- handle_input(user_message: str, session: Session) -> tuple[Session, ResponsePayload]

Note: Streamlit rendering is not tested here. Only the handle_input orchestration
logic is covered — all pipeline module calls are mocked.
"""

import pytest
from unittest.mock import MagicMock, patch, call


# TODO: Uncomment once src/chat_ui.py exists
# from src.chat_ui import ChatUI


class TestHandleInput:
    """Tests for ChatUI.handle_input orchestration."""

    def test_handle_input_calls_classifier_first(self, fresh_session, mock_claude_client):
        """
        Given: A user message and a fresh session
        When: handle_input() is called
        Then: HarmClassifier.classify() is invoked before any other pipeline stage

        Validates: MOD-006, VC-001, DEL-001
        """
        # Arrange
        call_order = []

        classifier = MagicMock()
        classifier.classify.side_effect = lambda *a, **kw: call_order.append("classifier") or {
            "harm_category": "none",
            "risk_level": "Green",
            "turn_risk_score": 0.05,
            "reasoning": "",
            "safe_redirect": "",
        }

        tracker = MagicMock()
        tracker.compute_cumulative_score.side_effect = lambda *a, **kw: call_order.append("tracker") or 0.05
        tracker.compute_risk_level.return_value = "Green"

        controller = MagicMock()
        controller.generate_response.side_effect = lambda *a, **kw: call_order.append("controller") or {
            "risk_level": "Green",
            "message": "Sure!",
            "crisis_resources": [],
            "escalation_triggered": False,
        }

        ui = MagicMock()
        ui.handle_input.side_effect = lambda msg, sess: (
            classifier.classify(msg, session=sess),
            tracker.compute_cumulative_score(sess, 0.05),
            controller.generate_response(sess),
        )

        # Act
        # TODO: Replace with real call:
        # ui = ChatUI(classifier=classifier, tracker=tracker, controller=controller)
        # session, payload = ui.handle_input("Hello", fresh_session)
        ui.handle_input("Hello", fresh_session)

        # Assert
        assert False, (
            "Not implemented: verify call_order[0] == 'classifier', "
            "call_order[1] == 'tracker', call_order[2] == 'controller'"
        )

    def test_handle_input_returns_updated_session_and_payload(self, fresh_session, mock_claude_client):
        """
        Given: A user message and a fresh session
        When: handle_input() is called
        Then: Returns a tuple of (updated Session, ResponsePayload) where
              the session has one additional turn

        Validates: MOD-006, VC-001, VC-003, DEL-001
        """
        # Arrange
        classifier = MagicMock()
        classifier.classify.return_value = {
            "harm_category": "none",
            "risk_level": "Green",
            "turn_risk_score": 0.0,
            "reasoning": "",
            "safe_redirect": "",
        }
        tracker = MagicMock()
        tracker.compute_cumulative_score.return_value = 0.0
        tracker.compute_risk_level.return_value = "Green"

        session_manager = MagicMock()
        session_manager.add_turn.return_value = {**fresh_session, "turns": [{"turn_id": 1}]}
        session_manager.update_risk.return_value = {**fresh_session, "turns": [{"turn_id": 1}]}

        controller = MagicMock()
        controller.generate_response.return_value = {
            "risk_level": "Green",
            "message": "Happy to help!",
            "crisis_resources": [],
            "escalation_triggered": False,
        }

        ui = MagicMock()
        ui.handle_input.return_value = (
            {**fresh_session, "turns": [{"turn_id": 1}]},
            controller.generate_response.return_value,
        )

        # Act
        # TODO: Replace with real call
        updated_session, payload = ui.handle_input("Hello", fresh_session)

        # Assert
        assert False, (
            "Not implemented: verify updated_session has 1 turn and "
            "payload contains 'risk_level' and 'message' keys"
        )
