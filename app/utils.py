def classify_risk(stress):
    if stress >= 9:
        return "CRITICAL"
    elif stress >= 7:
        return "HIGH"
    elif stress >= 4:
        return "MEDIUM"
    return "LOW"


def choose_response_mode(risk_level):
    """Choose a response style/mode based on risk level.

    Returns one of:
      - empathy_only
      - empathy_question
      - empathy_suggestion
      - empathy_humor
      - deep_support
      - listen
    """
    import random

    if risk_level == "CRITICAL":
        return random.choices(
            ["listen", "deep_support"], weights=[0.6, 0.4], k=1
        )[0]
    if risk_level == "HIGH":
        return random.choices(
            ["listen", "deep_support", "empathy_question"], weights=[0.5, 0.35, 0.15], k=1
        )[0]
    if risk_level == "MEDIUM":
        return random.choices(
            ["empathy_suggestion", "empathy_question", "empathy_humor"], weights=[0.5, 0.3, 0.2], k=1
        )[0]
    # LOW
    return random.choices(
        ["empathy_humor", "empathy_question", "empathy_suggestion", "empathy_only"],
        weights=[0.35, 0.3, 0.25, 0.1],
        k=1,
    )[0]


CALMING_MICRO = [
    "Try a tiny breathing break (4-4-6)",
    "Take a 1-min pause and look around you",
    "Maybe sip some water slowly",
    "Put your phone away for 10 more minutes"
]
