"""
Unit tests for PatternRiskTracker (MOD-003).
"""

import pytest
from datetime import datetime, timezone

from src import pattern_risk_tracker as prt
from src.models import ClassificationResult, Session, Turn


def _make_session_with_scores(*scores):
    """Build a session whose turns have the given turn_risk_scores."""
    turns = []
    for i, score in enumerate(scores):
        turns.append(Turn(
            turn_id=i,
            user_message=f"msg {i}",
            classification=ClassificationResult(
                harm_category="none", risk_level="Green",
                turn_risk_score=score, safe_redirect="",
            ),
            timestamp=datetime.now(timezone.utc),
        ))
    return Session(
        session_id="test",
        user_age_group="minor",
        turns=turns,
    )


class TestComputeRiskLevel:

    @pytest.mark.parametrize("score,expected", [
        (0.0, "Green"),
        (0.29, "Green"),
        (0.30, "Yellow"),
        (0.54, "Yellow"),
        (0.55, "Orange"),
        (0.79, "Orange"),
        (0.80, "Red"),
        (1.0, "Red"),
    ])
    def test_threshold_boundaries(self, score, expected):
        assert prt.compute_risk_level(score) == expected


class TestComputeTurnScore:

    def test_later_turn_higher_weight_than_earlier(self):
        early = prt.compute_turn_score(0, 0.30)
        late = prt.compute_turn_score(4, 0.30)
        assert late > early

    def test_turn_score_scales_linearly(self):
        assert prt.compute_turn_score(0, 0.5) == pytest.approx(0.5)
        assert prt.compute_turn_score(1, 0.5) == pytest.approx(1.0)
        assert prt.compute_turn_score(2, 0.5) == pytest.approx(1.5)


class TestUpdate:

    def test_empty_session_stays_green(self, fresh_session):
        result = ClassificationResult(
            harm_category="none", risk_level="Green",
            turn_risk_score=0.0, safe_redirect="",
        )
        session = prt.update(fresh_session, result)
        assert session.risk_level == "Green"
        assert session.cumulative_risk_score == pytest.approx(0.0)

    def test_score_after_multiple_turns_exceeds_single_turn(self):
        one_turn = _make_session_with_scores(0.40)
        three_turns = _make_session_with_scores(0.40, 0.40, 0.40)
        result = ClassificationResult(
            harm_category="none", risk_level="Yellow",
            turn_risk_score=0.40, safe_redirect="",
        )
        prt.update(one_turn, result)
        prt.update(three_turns, result)
        assert three_turns.cumulative_risk_score > one_turn.cumulative_risk_score

    def test_high_scores_eventually_reach_red(self):
        session = _make_session_with_scores(0.9, 0.9, 0.9)
        result = ClassificationResult(
            harm_category="self_harm", risk_level="Red",
            turn_risk_score=0.9, safe_redirect="",
        )
        prt.update(session, result)
        assert session.risk_level == "Red"

    def test_cumulative_score_clamped_to_one(self):
        session = _make_session_with_scores(1.0, 1.0, 1.0)
        result = ClassificationResult(
            harm_category="self_harm", risk_level="Red",
            turn_risk_score=1.0, safe_redirect="",
        )
        prt.update(session, result)
        assert session.cumulative_risk_score <= 1.0
