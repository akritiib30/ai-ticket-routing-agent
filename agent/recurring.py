from .models import RecurringResult


def detect(retrieved_tickets):
    """
    Detect whether the current issue may be recurring.

    For the MVP, an issue is considered recurring when
    at least 3 similar historical tickets are found.
    """

    related_tickets = [
        ticket
        for ticket in retrieved_tickets
        if ticket.similarity >= 0.20
    ]

    cluster_size = len(related_tickets)

    return RecurringResult(
        is_recurring=cluster_size >= 3,
        cluster_size=cluster_size,
    )