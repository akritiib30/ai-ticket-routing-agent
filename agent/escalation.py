def should_escalate(confidence_result) -> bool:
    """
    Escalate tickets with low confidence.
    """

    return confidence_result.tier == "low"


def needs_review_flag(confidence_result) -> bool:
    """
    Flag medium-confidence tickets for human review.
    """

    return confidence_result.tier == "medium"