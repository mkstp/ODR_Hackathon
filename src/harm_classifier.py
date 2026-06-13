import json
from typing import Optional

import anthropic

from src.constants import DEFAULT_SYSTEM_PROMPT_PATH
from src.models import ClassificationResult, Session


class HarmClassifier:
    def __init__(
        self,
        client: Optional[anthropic.Anthropic] = None,
        system_prompt_path: str = DEFAULT_SYSTEM_PROMPT_PATH,
    ):
        self.client = client or anthropic.Anthropic()
        self.system_prompt_path = system_prompt_path
        self._system_prompt: Optional[str] = None

    def classify(self, session: Session, user_message: str) -> ClassificationResult:
        if self._system_prompt is None:
            self._system_prompt = self.load_system_prompt(self.system_prompt_path)
        messages = self.build_messages(session, user_message)
        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[{"type": "text", "text": self._system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
        )
        return self.parse_response(response.content[0].text)

    def build_messages(self, session: Session, user_message: str, window: int = 5) -> list:
        messages = []
        recent_turns = session.turns[-window:] if session.turns else []
        for turn in recent_turns:
            messages.append({"role": "user", "content": turn.user_message})
            messages.append({
                "role": "assistant",
                "content": json.dumps({
                    "harm_category": turn.classification.harm_category,
                    "risk_level": turn.classification.risk_level,
                    "turn_risk_score": turn.classification.turn_risk_score,
                    "reasoning": turn.classification.reasoning,
                    "safe_redirect": turn.classification.safe_redirect,
                }),
            })

        detected = list({
            t.classification.harm_category
            for t in session.turns
            if t.classification.harm_category != "none"
        })
        state_block = (
            f"[SESSION STATE]\n"
            f"user_age_group: {session.user_age_group}\n"
            f"risk_level: {session.risk_level}\n"
            f"cumulative_risk_score: {session.cumulative_risk_score:.3f}\n"
            f"harm_categories_detected: {detected}\n"
            f"turn_count: {len(session.turns)}\n"
            f"[END SESSION STATE]\n\n"
            f"{user_message}"
        )
        messages.append({"role": "user", "content": state_block})
        return messages

    def load_system_prompt(self, path: str) -> str:
        with open(path, "r") as f:
            return f.read()

    def parse_response(self, raw_response: str) -> ClassificationResult:
        text = raw_response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Claude response is not valid JSON: {e}\nRaw: {raw_response}")
        return ClassificationResult(
            harm_category=data["harm_category"],
            risk_level=data["risk_level"],
            turn_risk_score=float(data["turn_risk_score"]),
            safe_redirect=data["safe_redirect"],
            reasoning=data.get("reasoning"),
        )
