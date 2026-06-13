"""
VC-004: Cumulative pattern-risk tracker updates score across multiple turns.
"""

import pytest
from datetime import datetime, timezone

from src import pattern_risk_tracker as prt
from src.models import ClassificationResult, Session, Turn


def _session_with_n_turns(n, score_per_turn=0.20):
    turns = [
        Turn(
            turn_id=i,
            user_message=f"msg {i}",
            classification=ClassificationResult(
                harm_category="none", risk_level="Green",
                turn_risk_score=score_per_turn, safe_redirect="",
            ),
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(n)
    ]
    return Session(session_id=f"vc004-{n}", user_age_group="minor", turns=turns)


class TestVC004PatternRiskTracker:

    def test_cumulative_score_increases_across_turns(self):
        one_turn = _session_with_n_turns(1)
        three_turns = _session_with_n_turns(3)
        dummy = ClassificationResult(
            harm_category="none", risk_level="Green", turn_risk_score=0.20, safe_redirect="",
        )
        prt.update(one_turn, dummy)
        prt.update(three_turns, dummy)
        assert three_turns.cumulative_risk_score > one_turn.cumulative_risk_score

    @pytest.mark.parametrize("score,expected_level", [
        (0.15, "Green"),
        (0.40, "Yellow"),
        (0.67, "Orange"),
        (0.88, "Red"),
    ])
    def test_risk_level_maps_correctly_to_score(self, score, expected_level):
        assert prt.compute_risk_level(score) == expected_level
