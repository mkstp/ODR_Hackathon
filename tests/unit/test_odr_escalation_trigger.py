"""
Unit tests for ODREscalationTrigger (MOD-005).
"""

import json
import pytest
from pathlib import Path

from src import odr_escalation_trigger as odt
from src.models import EscalationRecord


class TestBuildRecord:

    def test_build_record_contains_session_id(self, red_session):
        record = odt.build_record(red_session)
        assert record.session_id == red_session.session_id

    def test_build_record_contains_timestamp(self, red_session):
        record = odt.build_record(red_session)
        assert record.timestamp is not None
        assert record.timestamp.isoformat()

    def test_build_record_lists_harm_categories_from_turns(self, red_session):
        record = odt.build_record(red_session)
        assert "self_harm" in record.harm_categories_detected

    def test_build_record_has_correct_turn_count(self, red_session):
        record = odt.build_record(red_session)
        assert record.turn_count == len(red_session.turns)

    def test_build_record_final_risk_score_matches_session(self, red_session):
        record = odt.build_record(red_session)
        assert record.final_risk_score == pytest.approx(red_session.cumulative_risk_score)


class TestTrigger:

    def test_trigger_returns_record_for_unescalated_red_session(self, red_session):
        record = odt.trigger(red_session)
        assert isinstance(record, EscalationRecord)
        assert record.session_id == red_session.session_id

    def test_trigger_returns_none_if_already_escalated(self, red_session):
        red_session.escalated = True
        result = odt.trigger(red_session)
        assert result is None


class TestLogRecord:

    def test_log_record_appends_valid_json_line(self, tmp_path, red_session):
        log_file = tmp_path / "escalation_log.jsonl"
        record = odt.build_record(red_session)
        odt.log_record(record, log_file)

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["session_id"] == red_session.session_id
        assert "timestamp" in data
        assert "harm_categories_detected" in data

    def test_log_record_appends_not_overwrites(self, tmp_path, red_session):
        log_file = tmp_path / "escalation_log.jsonl"
        record = odt.build_record(red_session)
        odt.log_record(record, log_file)
        odt.log_record(record, log_file)

        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            json.loads(line)
