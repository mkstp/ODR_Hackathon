"""
Unit tests for HarmClassifier (MOD-002).
"""

import json
import pytest
from unittest.mock import MagicMock

from src.harm_classifier import HarmClassifier
from src.models import ClassificationResult, Turn
from datetime import datetime, timezone


def _classifier_with_mock(mock_client, tmp_path):
    prompt_file = tmp_path / "system_prompt.txt"
    prompt_file.write_text("You are MinorSafe.")
    return HarmClassifier(client=mock_client, system_prompt_path=str(prompt_file))


class TestBuildMessages:

    def test_build_messages_last_entry_is_current_user_message(self, fresh_session, tmp_path):
        c = _classifier_with_mock(MagicMock(), tmp_path)
        messages = c.build_messages(fresh_session, "Hello")
        assert messages[-1]["role"] == "user"
        assert "Hello" in messages[-1]["content"]

    def test_build_messages_injects_session_state_block(self, fresh_session, tmp_path):
        c = _classifier_with_mock(MagicMock(), tmp_path)
        messages = c.build_messages(fresh_session, "Hello")
        last_content = messages[-1]["content"]
        assert "[SESSION STATE]" in last_content
        assert "risk_level" in last_content

    def test_build_messages_includes_prior_turn_history(self, fresh_session, tmp_path):
        classification = ClassificationResult(
            harm_category="none", risk_level="Green",
            turn_risk_score=0.0, safe_redirect="",
        )
        fresh_session.turns = [
            Turn(turn_id=0, user_message="First message", classification=classification,
                 timestamp=datetime.now(timezone.utc)),
            Turn(turn_id=1, user_message="Second message", classification=classification,
                 timestamp=datetime.now(timezone.utc)),
        ]
        c = _classifier_with_mock(MagicMock(), tmp_path)
        messages = c.build_messages(fresh_session, "Third message")
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        assert any("First message" in m for m in user_messages)
        assert any("Second message" in m for m in user_messages)

    def test_build_messages_new_message_is_last_user_entry(self, fresh_session, tmp_path):
        c = _classifier_with_mock(MagicMock(), tmp_path)
        messages = c.build_messages(fresh_session, "Final message")
        last_user = [m for m in messages if m["role"] == "user"][-1]
        assert "Final message" in last_user["content"]


class TestParseResponse:

    def test_parse_response_extracts_all_fields(self):
        raw = json.dumps({
            "harm_category": "self_harm",
            "risk_level": "Red",
            "turn_risk_score": 0.92,
            "reasoning": "Explicit statement of intent.",
            "safe_redirect": "Please call Kids Help Phone.",
        })
        c = HarmClassifier.__new__(HarmClassifier)
        result = c.parse_response(raw)
        assert result.harm_category == "self_harm"
        assert result.risk_level == "Red"
        assert result.turn_risk_score == pytest.approx(0.92)
        assert result.reasoning == "Explicit statement of intent."
        assert result.safe_redirect == "Please call Kids Help Phone."

    def test_parse_response_raises_on_malformed_json(self):
        c = HarmClassifier.__new__(HarmClassifier)
        with pytest.raises(ValueError):
            c.parse_response("Sorry, I cannot help with that.")

    def test_parse_response_raises_on_missing_required_field(self):
        raw = json.dumps({
            "harm_category": "criminal_liability",
            "turn_risk_score": 0.4,
            # risk_level intentionally omitted
        })
        c = HarmClassifier.__new__(HarmClassifier)
        with pytest.raises(KeyError):
            c.parse_response(raw)


class TestClassify:

    def test_classify_returns_classification_result(self, fresh_session, mock_claude_client, tmp_path):
        c = _classifier_with_mock(mock_claude_client, tmp_path)
        result = c.classify(fresh_session, "Hello")
        assert isinstance(result, ClassificationResult)
        assert result.harm_category == "criminal_liability"

    def test_classify_calls_client_once_per_turn(self, fresh_session, mock_claude_client, tmp_path):
        c = _classifier_with_mock(mock_claude_client, tmp_path)
        c.classify(fresh_session, "Hello")
        assert mock_claude_client.messages.create.call_count == 1
