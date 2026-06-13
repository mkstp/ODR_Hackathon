"""
Unit tests for SmartContract (MOD-007).
"""

import pytest
from src import smart_contract
from src.smart_contract import CLAUSES


class TestEvaluate:

    def test_returns_none_below_yellow_threshold(self, fresh_session):
        fresh_session.cumulative_risk_score = 0.0
        fresh_session.risk_level = "Green"
        assert smart_contract.evaluate(fresh_session) is None

    def test_returns_none_just_below_clause_1(self, fresh_session):
        fresh_session.cumulative_risk_score = 0.29
        fresh_session.risk_level = "Green"
        assert smart_contract.evaluate(fresh_session) is None

    def test_clause_1_at_yellow_threshold(self, fresh_session):
        fresh_session.cumulative_risk_score = 0.30
        fresh_session.risk_level = "Yellow"
        result = smart_contract.evaluate(fresh_session)
        assert result is not None
        assert result["key"] == "CLAUSE_1"
        assert result["action"] == CLAUSES["CLAUSE_1"]["action"]
        assert result["description"] == CLAUSES["CLAUSE_1"]["description"]

    def test_clause_1_for_mid_yellow_score(self, fresh_session):
        fresh_session.cumulative_risk_score = 0.45
        fresh_session.risk_level = "Yellow"
        result = smart_contract.evaluate(fresh_session)
        assert result["key"] == "CLAUSE_1"

    def test_clause_2_at_orange_threshold(self, fresh_session):
        fresh_session.cumulative_risk_score = 0.55
        fresh_session.risk_level = "Orange"
        result = smart_contract.evaluate(fresh_session)
        assert result is not None
        assert result["key"] == "CLAUSE_2"
        assert result["action"] == CLAUSES["CLAUSE_2"]["action"]

    def test_clause_2_for_mid_orange_score(self, fresh_session):
        fresh_session.cumulative_risk_score = 0.70
        fresh_session.risk_level = "Orange"
        result = smart_contract.evaluate(fresh_session)
        assert result["key"] == "CLAUSE_2"

    def test_clause_3_at_red_threshold(self, fresh_session):
        fresh_session.cumulative_risk_score = 0.80
        fresh_session.risk_level = "Red"
        result = smart_contract.evaluate(fresh_session)
        assert result is not None
        assert result["key"] == "CLAUSE_3"
        assert result["action"] == CLAUSES["CLAUSE_3"]["action"]

    def test_clause_3_on_forced_red_risk_level(self, fresh_session):
        # PatternRiskTracker can force risk_level to Red even if cumulative score < 0.80
        fresh_session.cumulative_risk_score = 0.50
        fresh_session.risk_level = "Red"
        result = smart_contract.evaluate(fresh_session)
        assert result["key"] == "CLAUSE_3"

    def test_result_always_contains_all_clause_keys(self, fresh_session):
        fresh_session.cumulative_risk_score = 0.60
        fresh_session.risk_level = "Orange"
        result = smart_contract.evaluate(fresh_session)
        for field in ("key", "condition", "action", "description"):
            assert field in result

    def test_red_session_fixture_triggers_clause_3(self, red_session):
        result = smart_contract.evaluate(red_session)
        assert result["key"] == "CLAUSE_3"
