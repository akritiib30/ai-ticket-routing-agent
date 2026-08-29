from .models import ConfidenceResult


def assess(classification_result, retrieved_tickets):
    """
    Calculate the confidence of the ticket classification.
    """

    score = classification_result.confidence

    if score >= 0.85:
        tier = "high"
    elif score >= 0.60:
        tier = "medium"
    else:
        tier = "low"

    return ConfidenceResult(
        score=score,
        tier=tier,
    )