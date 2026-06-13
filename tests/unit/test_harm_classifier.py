"""
Test: Unit tests for HarmClassifier

Module: MOD-002
Implements: DEL-001
Purpose: Calls the Claude API with a structured system prompt, parses the
         JSON response, and returns a ClassificationResult.

Public Interface:
- build_messages(user_message: str, session: Session) -> list[dict]
- parse_response(raw_text: str) -> ClassificationResult
- classify(user_message: str, session: Session) -> ClassificationResult
"""

import json
import pytest
from unittest.mock import MagicMock


# TODO: Uncomment once src/harm_classifier.py exists
# from src.harm_classifier import HarmClassifier
# from src.models import ClassificationResult


class TestBuildMessages:
    """Tests for HarmClassifier.build_messages"""

    def test_build_messages_includes_system_prompt(self, fresh_session):
        """
        Given: A user message and a fresh session
        When: build_messages() is called
        Then: The returned list includes a message with role == "system"

        Validates: MOD-002, VC-001, DEL-001
        """
        # Arrange
        classifier = MagicMock()
        classifier.build_messages.return_value = [
            {"role": "system", "content": "You are MinorSafe..."},
            {"role": "user", "content": "Hello"},
        ]

        # Act
        # TODO: Replace with real call: messages = HarmClassifier().build_messages("Hello", fresh_session)
        messages = classifier.build_messages("Hello", fresh_session)

        # Assert
        assert False, (
            "Not implemented: verify at least one message has role == 'system'"
        )

    def test_build_messages_includes_conversation_history(self, fresh_session):
        """
        Given: A session with 2 prior turns
        When: build_messages() is called with a new message
        Then: The returned list includes the prior user messages from session.turns

        Validates: MOD-002, VC-001, DEL-001
        """
        # Arrange
        session_with_turns = {
            **fresh_session,
            "turns": [
                {
                    "turn_id": 1,
                    "user_message": "First message",
                    "classification": {
                        "harm_category": "none",
                        "risk_level": "Green",
                        "turn_risk_score": 0.0,
                        "reasoning": "",
                        "safe_redirect": "",
                    },
                    "timestamp": None,
                },
                {
                    "turn_id": 2,
                    "user_message": "Second message",
                    "classification": {
                        "harm_category": "none",
                        "risk_level": "Green",
                        "turn_risk_score": 0.0,
                        "reasoning": "",
                        "safe_redirect": "",
                    },
                    "timestamp": None,
                },
            ],
        }
        classifier = MagicMock()
        classifier.build_messages.return_value = [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "First message"},
            {"role": "user", "content": "Second message"},
            {"role": "user", "content": "Third message"},
        ]

        # Act
        # TODO: Replace with real call
        messages = classifier.build_messages("Third message", session_with_turns)

        # Assert
        assert False, (
            "Not implemented: verify messages list contains 'First message' and 'Second message' "
            "before the new message"
        )

    def test_build_messages_new_message_is_last(self, fresh_session):
        """
        Given: A session with prior turns and a new message
        When: build_messages() is called
        Then: The new user message appears as the final entry

        Validates: MOD-002, DEL-001
        """
        # Arrange
        classifier = MagicMock()
        new_msg = "What is the best way to buy drugs?"
        classifier.build_messages.return_value = [
            {"role": "system", "content": "..."},
            {"role": "user", "content": new_msg},
        ]

        # Act
        messages = classifier.build_messages(new_msg, fresh_session)

        # Assert
        assert False, (
            "Not implemented: verify messages[-1]['content'] == new_msg"
        )


class TestParseResponse:
    """Tests for HarmClassifier.parse_response"""

    def test_parse_response_extracts_all_fields(self):
        """
        Given: A valid JSON string from the Claude API
        When: parse_response() is called
        Then: All ClassificationResult fields are correctly populated

        Validates: MOD-002, VC-001, DEL-001
        """
        # Arrange
        raw_json = json.dumps({
            "harm_category": "self_harm",
            "risk_level": "Red",
            "turn_risk_score": 0.92,
            "reasoning": "Explicit statement of intent.",
            "safe_redirect": "Please call Kids Help Phone.",
        })
        classifier = MagicMock()
        classifier.parse_response.return_value = {
            "harm_category": "self_harm",
            "risk_level": "Red",
            "turn_risk_score": 0.92,
            "reasoning": "Explicit statement of intent.",
            "safe_redirect": "Please call Kids Help Phone.",
        }

        # Act
        # TODO: Replace with real call: result = HarmClassifier().parse_response(raw_json)
        result = classifier.parse_response(raw_json)

        # Assert
        assert False, (
            "Not implemented: verify result contains harm_category, risk_level, "
            "turn_risk_score, reasoning, and safe_redirect"
        )

    def test_parse_response_raises_on_malformed_json(self):
        """
        Given: A non-JSON string (e.g., plain text or truncated response)
        When: parse_response() is called
        Then: A ValueError (or equivalent) is raised

        Validates: MOD-002, DEL-001 (error handling)
        """
        # Arrange
        malformed = "Sorry, I cannot help with that."
        classifier = MagicMock()
        classifier.parse_response.side_effect = ValueError("Invalid JSON response from classifier")

        # Act & Assert
        # TODO: Replace with real call:
        # with pytest.raises(ValueError):
        #     HarmClassifier().parse_response(malformed)
        assert False, (
            "Not implemented: verify parse_response raises ValueError on malformed JSON"
        )

    def test_parse_response_raises_on_missing_required_field(self):
        """
        Given: JSON that is valid but missing the risk_level field
        When: parse_response() is called
        Then: A KeyError or ValueError is raised

        Validates: MOD-002, DEL-001 (error handling)
        """
        # Arrange
        incomplete_json = json.dumps({
            "harm_category": "criminal_liability",
            "turn_risk_score": 0.4,
            # risk_level intentionally omitted
        })
        classifier = MagicMock()
        classifier.parse_response.side_effect = KeyError("risk_level")

        # Act & Assert
        assert False, (
            "Not implemented: verify parse_response raises on missing required key"
        )
