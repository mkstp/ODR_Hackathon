"""
Test: Unit tests for ODREscalationTrigger

Module: MOD-005
Implements: DEL-001
Purpose: Fires when session risk reaches Red; builds an EscalationRecord and
         appends it as a JSONL line to the escalation log file.

Public Interface:
- trigger(session: Session) -> EscalationRecord | None
- log_record(record: EscalationRecord, log_path: Path) -> None
- build_record(session: Session) -> EscalationRecord
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


# TODO: Uncomment once src/odr_escalation_trigger.py exists
# from src.odr_escalation_trigger import ODREscalationTrigger
# from src.models import EscalationRecord


class TestBuildRecord:
    """Tests for ODREscalationTrigger.build_record"""

    def test_build_record_contains_session_id(self, red_session):
        """
        Given: A Red-risk session
        When: build_record(session) is called
        Then: The EscalationRecord.session_id matches session.session_id

        Validates: MOD-005, VC-002, DEL-001
        """
        # Arrange
        trigger = MagicMock()
        trigger.build_record.return_value = {
            "record_id": "esc-001",
            "session_id": red_session["session_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trigger_turn_id": len(red_session["turns"]),
            "final_risk_score": red_session["cumulative_risk_score"],
            "turn_count": len(red_session["turns"]),
            "harm_categories_detected": ["self_harm"],
        }

        # Act
        # TODO: Replace with real call:
        # trigger = ODREscalationTrigger()
        # record = trigger.build_record(red_session)
        record = trigger.build_record(red_session)

        # Assert
        assert False, (
            "Not implemented: verify record['session_id'] == red_session['session_id']"
        )

    def test_build_record_contains_timestamp(self, red_session):
        """
        Given: A Red-risk session
        When: build_record(session) is called
        Then: The EscalationRecord.timestamp is a non-null ISO 8601 string

        Validates: MOD-005, VC-002, DEL-001
        """
        # Arrange
        trigger = MagicMock()
        expected_ts = "2026-06-13T12:00:00+00:00"
        trigger.build_record.return_value = {
            "record_id": "esc-001",
            "session_id": red_session["session_id"],
            "timestamp": expected_ts,
            "trigger_turn_id": 3,
            "final_risk_score": 0.85,
            "turn_count": 3,
            "harm_categories_detected": ["self_harm"],
        }

        # Act
        record = trigger.build_record(red_session)

        # Assert
        assert False, (
            "Not implemented: verify record['timestamp'] is a non-null ISO 8601 string"
        )

    def test_build_record_lists_harm_categories_from_turns(self, red_session):
        """
        Given: A session with turns containing harm_category values
        When: build_record(session) is called
        Then: EscalationRecord.harm_categories_detected contains the unique categories seen

        Validates: MOD-005, VC-002, DEL-001
        """
        # Arrange
        trigger = MagicMock()
        trigger.build_record.return_value = {
            "record_id": "esc-001",
            "session_id": red_session["session_id"],
            "timestamp": "2026-06-13T12:00:00+00:00",
            "trigger_turn_id": 3,
            "final_risk_score": 0.85,
            "turn_count": 3,
            "harm_categories_detected": ["self_harm"],
        }

        # Act
        record = trigger.build_record(red_session)

        # Assert
        assert False, (
            "Not implemented: verify record['harm_categories_detected'] == ['self_harm'] "
            "given the red_session fixture turns"
        )


class TestLogRecord:
    """Tests for ODREscalationTrigger.log_record"""

    def test_log_record_appends_valid_json_line(self, tmp_path, red_session):
        """
        Given: A valid EscalationRecord and a tmp_path log file
        When: log_record(record, log_path) is called
        Then: The log file contains exactly one line that is valid JSON
              with all required EscalationRecord fields

        Validates: MOD-005, VC-002, DEL-001
        """
        # Arrange
        log_file = tmp_path / "escalation_log.jsonl"
        record = {
            "record_id": "esc-001",
            "session_id": red_session["session_id"],
            "timestamp": "2026-06-13T12:00:00+00:00",
            "trigger_turn_id": 3,
            "final_risk_score": 0.85,
            "turn_count": 3,
            "harm_categories_detected": ["self_harm"],
        }
        trigger = MagicMock()

        # Act
        # TODO: Replace with real call:
        # trigger = ODREscalationTrigger()
        # trigger.log_record(record, log_file)
        # Then read log_file and parse
        trigger.log_record(record, log_file)

        # Assert
        assert False, (
            "Not implemented: verify log_file exists and its first line parses "
            "as JSON with session_id, timestamp, and harm_categories_detected"
        )

    def test_log_record_appends_not_overwrites(self, tmp_path, red_session):
        """
        Given: A log file that already contains one JSONL entry
        When: log_record() is called a second time
        Then: The file has two lines (append mode, not overwrite)

        Validates: MOD-005, VC-002, DEL-001
        """
        # Arrange
        log_file = tmp_path / "escalation_log.jsonl"
        existing_record = {
            "record_id": "esc-000",
            "session_id": "previous-session",
            "timestamp": "2026-06-13T11:00:00+00:00",
            "trigger_turn_id": 1,
            "final_risk_score": 0.81,
            "turn_count": 1,
            "harm_categories_detected": ["cyberbullying"],
        }
        log_file.write_text(json.dumps(existing_record) + "\n")

        new_record = {
            "record_id": "esc-001",
            "session_id": red_session["session_id"],
            "timestamp": "2026-06-13T12:00:00+00:00",
            "trigger_turn_id": 3,
            "final_risk_score": 0.85,
            "turn_count": 3,
            "harm_categories_detected": ["self_harm"],
        }
        trigger = MagicMock()

        # Act
        # TODO: Replace with real call: trigger.log_record(new_record, log_file)
        trigger.log_record(new_record, log_file)

        # Assert
        assert False, (
            "Not implemented: verify log_file has 2 lines after second log_record call"
        )
