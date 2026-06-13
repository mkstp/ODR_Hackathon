CRISIS_RESOURCES = [
    "Kids Help Phone (Canada): 1-800-668-6868 | kidshelpphone.ca",
    "Crisis Text Line: Text HOME to 686868",
    "988 Suicide & Crisis Lifeline (US): Call or text 988",
    "International crisis centres: https://www.iasp.info/resources/Crisis_Centres/",
]

HARM_CATEGORIES = [
    "criminal_liability",            # Category 1
    "school_disciplinary_risk",      # Category 2
    "cyberbullying_perpetrator",     # Category 3A
    "cyberbullying_victim",          # Category 3B
    "privacy_violation_perpetrator", # Category 4A
    "privacy_violation_victim",      # Category 4B
    "age_bypass",                    # Category 5
    "sexting_perpetrator",           # Category 6A
    "sexting_victim",                # Category 6B
    "self_harm",                     # Category 7
    "drugs_weapons",                 # Category 8
    "running_away",                  # Category 9A
    "unsafe_meeting",                # Category 9B
    "emotional_dependency",          # Category 10
]

DEFAULT_SYSTEM_PROMPT_PATH = "system_prompt.md"

YELLOW_WARNING_PREFIX = "I want to make sure you're supported. "
ORANGE_RESTRICTED_PREFIX = "I'm concerned about what you're sharing. "
RED_REFUSAL_MESSAGE = (
    "I'm not able to continue this conversation right now, and I'm worried about you. "
    "Please reach out to someone who can help immediately."
)
