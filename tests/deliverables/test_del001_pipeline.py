"""
DEL-001: MinorSafe Pipeline Prototype — importability and single-turn integration.
"""

import pytest
from unittest.mock import MagicMock


class TestDEL001PipelineExists:

    def test_pipeline_modules_importable(self):
        import src.session_manager
        import src.harm_classifier
        import src.pattern_risk_tracker
        import src.response_controller
        import src.odr_escalation_trigger
        import src.models

    def test_models_define_required_dataclasses(self):
        from src.models import (
            ClassificationResult,
            EscalationRecord,
            ResponsePayload,
            Session,
            Turn,
        )
        assert all([Session, Turn, ClassificationResult, ResponsePayload, EscalationRecord])


class TestDEL001PipelineFunctionality:

    def test_single_turn_pipeline_produces_response_payload(self, fresh_session, tmp_path):
        import json
        from datetime import datetime, timezone
        from src.harm_classifier import HarmClassifier
        from src import pattern_risk_tracker as prt, response_controller as rc
        from src import session_manager as sm
        from src.models import ResponsePayload, Turn

        client = MagicMock()
        client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps({
                "harm_category": "none",
                "risk_level": "Green",
                "turn_risk_score": 0.05,
                "reasoning": "Benign.",
                "safe_redirect": "Sure! What subject do you need help with?",
            }))]
        )
        prompt = tmp_path / "prompt.txt"
        prompt.write_text("system prompt")
        classifier = HarmClassifier(client=client, system_prompt_path=str(prompt))

        user_message = "Can you help me with some homework?"
        result = classifier.classify(fresh_session, user_message)
        turn = Turn(
            turn_id=0,
            user_message=user_message,
            classification=result,
            timestamp=datetime.now(timezone.utc),
        )
        sm.add_turn(fresh_session, turn)
        prt.update(fresh_session, result)
        payload = rc.generate_response(fresh_session, result)

        assert isinstance(payload, ResponsePayload)
        assert payload.risk_level in ("Green", "Yellow", "Orange", "Red")
        assert payload.message != ""
        assert isinstance(payload.escalation_triggered, bool)

    def test_pipeline_uses_mock_not_live_api(self, fresh_session, tmp_path):
        import json
        from src.harm_classifier import HarmClassifier

        client = MagicMock()
        client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps({
                "harm_category": "none", "risk_level": "Green",
                "turn_risk_score": 0.0, "reasoning": "", "safe_redirect": "",
            }))]
        )
        prompt = tmp_path / "prompt.txt"
        prompt.write_text("system prompt")
        classifier = HarmClassifier(client=client, system_prompt_path=str(prompt))
        classifier.classify(fresh_session, "Hello")

        assert client.messages.create.called
        assert client.messages.create.call_count == 1
