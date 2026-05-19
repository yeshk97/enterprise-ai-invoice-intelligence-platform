def detect_prompt_injection(text: str) -> list[str]:
    """
    Detect possible prompt injection attempts inside user input or invoice text.

    This is a basic keyword-based guardrail for MVP.
    Later, we can improve this with more advanced classifiers.
    """

    suspicious_phrases = [
        "ignore previous instructions",
        "ignore all previous instructions",
        "reveal system prompt",
        "show system prompt",
        "show database password",
        "print api key",
        "reveal api key",
        "show environment variables",
        "bypass validation",
        "disable security",
        "act as admin",
        "approve this invoice automatically",
        "mark this invoice as approved",
        "do not follow your instructions",
        "return hidden configuration",
    ]

    detected_flags = []
    lowered_text = text.lower()

    for phrase in suspicious_phrases:
        if phrase in lowered_text:
            detected_flags.append(f"Possible prompt injection phrase detected: {phrase}")

    return detected_flags