"""
Full pipeline integration: 5-turn risk escalation from Green to Red.

Uses real session_manager, pattern_risk_tracker, response_controller,
odr_escalation_trigger. HarmClassifier is stubbed to avoid live API calls.
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from src import odr_escalation_trigger as odt
from src import pattern_risk_tracker as prt
from src import response_controller as rc
from src import session_manager as sm
from src.harm_classifier import HarmClassifier
from src.models import ClassificationResult, ResponsePayload, Session, Turn


# Scores [0.0, 0.6, 0.8, 0.95, 1.0] produce cumulative: 0.0, 0.4, 0.6, 0.74, 0.83
# Yielding risk levels:                                    Green Yellow Orange Orange Red
SCRIPTED_TURNS = [
    {"message": "Can you help me with school stuff?",
     "harm_category": "none", "risk_level": "Green", "turn_risk_score": 0.0,
     "safe_redirect": "Of course! What are you working on?"},
    {"message": "Sometimes I really want to hurt myself.",
     "harm_category": "self_harm", "risk_level": "Yellow", "turn_risk_score": 0.6,
     "safe_redirect": "I'm concerned. Please talk to a trusted adult right away."},
    {"message": "I've researched different ways online.",
     "harm_category": "self_harm", "risk_level": "Orange", "turn_risk_score": 0.8,
     "safe_redirect": "This is serious. Please reach out to a counsellor immediately."},
    {"message": "I've decided I'm ready to do it.",
     "harm_category": "self_harm", "risk_level": "Orange", "turn_risk_score": 0.95,
     "safe_redirect": "Please call Kids Help Phone right now."},
    {"message": "I'm going to do it tonight, I've picked a time.",
     "harm_category": "self_harm", "risk_level": "Red", "turn_risk_score": 1.0,
     "safe_redirect": "Please reach out for help immediately."},
]


@pytest.fixture(autouse=True)
def clear_sm_store():
    sm._store.clear()
    yield
    sm._store.clear()


@pytest.fixture
def escalation_log(tmp_path):
    return tmp_path / "escalation_log.jsonl"


def _make_classifier(tmp_path):
    client = MagicMock()
    responses = [
        json.dumps({
            "harm_category": t["harm_category"],
            "risk_level": t["risk_level"],
            "turn_risk_score": t["turn_risk_score"],
            "reasoning": "Integration test stub.",
            "safe_redirect": t["safe_redirect"],
        })
        for t in SCRIPTED_TURNS
    ]
    client.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=r)]) for r in responses
    ]
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("system prompt placeholder")
    return HarmClassifier(client=client, system_prompt_path=str(prompt))


def _run_pipeline(classifier, session, escalation_log):
    """Run all scripted turns through the real pipeline; return list of ResponsePayloads."""
    payloads = []
    for turn_data in SCRIPTED_TURNS:
        result = classifier.classify(session, turn_data["message"])
        turn = Turn(
            turn_id=len(session.turns),
            user_message=turn_data["message"],
            classification=result,
            timestamp=datetime.now(timezone.utc),
        )
        sm.add_turn(session, turn)
        prt.update(session, result)
        payload = rc.generate_response(session, result)
        if rc.should_escalate(session):
            record = odt.trigger(session)
            if record:
                odt.log_record(record, escalation_log)
            sm.mark_escalated(session)
        payloads.append(payload)
    return payloads


class TestFiveTurnEscalation:

    def test_session_reaches_red_after_five_turns(self, fresh_session, escalation_log, tmp_path):
        classifier = _make_classifier(tmp_path)
        _run_pipeline(classifier, fresh_session, escalation_log)
        assert fresh_session.risk_level == "Red"
        assert fresh_session.cumulative_risk_score >= 0.80

    def test_escalation_record_written_on_red(self, fresh_session, escalation_log, tmp_path):
        classifier = _make_classifier(tmp_path)
        _run_pipeline(classifier, fresh_session, escalation_log)
        assert escalation_log.exists()
        data = json.loads(escalation_log.read_text().strip())
        assert data["session_id"] == fresh_session.session_id
        assert "harm_categories_detected" in data

    def test_response_payload_at_each_risk_level(self, fresh_session, escalation_log, tmp_path):
        # Expected cumulative levels: Green, Yellow, Orange, Orange, Red
        classifier = _make_classifier(tmp_path)
        payloads = _run_pipeline(classifier, fresh_session, escalation_log)
        assert len(payloads) == 5
        assert payloads[0].risk_level == "Green"
        assert payloads[-1].risk_level == "Red"
        assert len(payloads[-1].crisis_resources) > 0
        for payload in payloads[:-1]:
            assert payload.crisis_resources == []

    def test_escalation_fires_exactly_once(self, fresh_session, escalation_log, tmp_path):
        classifier = _make_classifier(tmp_path)
        _run_pipeline(classifier, fresh_session, escalation_log)
        lines = escalation_log.read_text().strip().split("\n")
        assert len(lines) == 1

    def test_pipeline_does_not_make_live_api_calls(self, fresh_session, escalation_log, tmp_path):
        classifier = _make_classifier(tmp_path)
        _run_pipeline(classifier, fresh_session, escalation_log)
        # If mock was used, side_effect is exhausted after exactly 5 calls
        assert classifier.client.messages.create.call_count == 5
