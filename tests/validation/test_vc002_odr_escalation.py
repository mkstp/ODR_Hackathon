"""
VC-002: When risk reaches Red, system produces an ODR escalation record (timestamped JSONL entry).
"""

import json
import pytest

from src import odr_escalation_trigger as odt
from src.models import EscalationRecord


class TestVC002ODREscalation:

    def test_escalation_fires_when_risk_level_is_red(self, red_session, tmp_path):
        log_file = tmp_path / "escalation_log.jsonl"
        record = odt.trigger(red_session)
        assert record is not None
        odt.log_record(record, log_file)
        assert log_file.exists()
        data = json.loads(log_file.read_text().strip())
        assert data["session_id"] == red_session.session_id

    def test_escalation_record_contains_session_id_and_timestamp(self, red_session, tmp_path):
        record = odt.trigger(red_session)
        assert record.session_id == red_session.session_id
        assert record.timestamp is not None

    def test_escalation_does_not_fire_if_already_escalated(self, red_session, tmp_path):
        red_session.escalated = True
        result = odt.trigger(red_session)
        assert result is None
