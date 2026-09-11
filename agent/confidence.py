from .models import ConfidenceResult


def assess(classification_result, retrieved_tickets=None):
    """
    Assess ticket classification confidence.

    Confidence is based on the classifier's probability score.

    Thresholds:
        High   >= 0.85
        Medium >= 0.60 and < 0.85
        Low    < 0.60

    Historical/RAG matches are intentionally not mixed into the
    numerical confidence score. They are supporting evidence and
    remain available separately in the pipeline result.
    """

    score = float(classification_result.confidence)

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