from .models import ResolutionResult


def generate(clean_text, retrieved_tickets):
    """Generate a resolution suggestion from similar historical tickets."""

    if not retrieved_tickets:
        return ResolutionResult(
            suggested_steps=(
                "No similar historical ticket was found. "
                "Please investigate the issue manually."
            )
        )

    best_ticket = retrieved_tickets[0]

    if best_ticket.resolution:
        suggestion = (
            f"Based on a similar historical ticket "
            f"({best_ticket.ticket_id}): "
            f"{best_ticket.resolution}"
        )
    else:
        suggestion = (
            "A similar ticket was found, but no previous "
            "resolution was recorded."
        )

    return ResolutionResult(
        suggested_steps=suggestion
    )