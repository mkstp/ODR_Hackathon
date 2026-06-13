"""
Unit tests for SessionManager (MOD-001).
"""

import pytest
from datetime import datetime, timezone

import src.session_manager as sm
from src.models import ClassificationResult, Session, Turn


@pytest.fixture(autouse=True)
def clear_store():
    sm._store.clear()
    yield
    sm._store.clear()


@pytest.fixture
def classification():
    return ClassificationResult(
        harm_category="none",
        risk_level="Green",
        turn_risk_score=0.0,
        safe_redirect="",
    )


class TestCreateSession:

    def test_create_session_sets_user_age_group(self):
        session = sm.create_session("minor")
        assert session.user_age_group == "minor"

    def test_create_session_initializes_green_risk(self):
        session = sm.create_session("minor")
        assert session.risk_level == "Green"
        assert session.cumulative_risk_score == 0.0

    def test_create_session_has_empty_turns_and_not_escalated(self):
        session = sm.create_session("minor")
        assert session.turns == []
        assert session.escalated is False

    def test_create_session_stores_in_memory(self):
        session = sm.create_session("minor")
        assert sm.get_session(session.session_id) is session


class TestAddTurn:

    def test_add_turn_increments_turn_count(self, fresh_session, classification):
        turn = Turn(turn_id=0, user_message="Hello", classification=classification,
                    timestamp=datetime.now(timezone.utc))
        result = sm.add_turn(fresh_session, turn)
        assert len(result.turns) == 1

    def test_add_turn_appends_in_order(self, fresh_session, classification):
        t1 = Turn(turn_id=0, user_message="first", classification=classification,
                  timestamp=datetime.now(timezone.utc))
        t2 = Turn(turn_id=1, user_message="second", classification=classification,
                  timestamp=datetime.now(timezone.utc))
        sm.add_turn(fresh_session, t1)
        sm.add_turn(fresh_session, t2)
        assert fresh_session.turns[0].user_message == "first"
        assert fresh_session.turns[1].user_message == "second"


class TestUpdateRisk:

    def test_update_risk_changes_level_and_score(self, fresh_session):
        result = sm.update_risk(fresh_session, "Yellow", 0.40)
        assert result.risk_level == "Yellow"
        assert result.cumulative_risk_score == pytest.approx(0.40)

    def test_update_risk_returns_same_session_object(self, fresh_session):
        result = sm.update_risk(fresh_session, "Orange", 0.65)
        assert result is fresh_session


class TestMarkEscalated:

    def test_mark_escalated_sets_flag_to_true(self, red_session):
        result = sm.mark_escalated(red_session)
        assert result.escalated is True

    def test_mark_escalated_returns_same_session_object(self, red_session):
        result = sm.mark_escalated(red_session)
        assert result is red_session
