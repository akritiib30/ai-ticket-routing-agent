from .models import RetrievedTicket


class Retriever:
    """
    Simple keyword-based retrieval for the MVP.

    Later, we will upgrade this to semantic embeddings + FAISS
    for proper RAG retrieval.
    """

    def __init__(self, tickets):
        self.tickets = tickets

    def search(self, query: str, top_k: int = 3):
        """Find the most similar historical tickets."""

        query_words = set(query.lower().split())

        scored_tickets = []

        for ticket in self.tickets:
            ticket_words = set(ticket["text"].lower().split())

            # Calculate word overlap
            common_words = query_words.intersection(ticket_words)

            if query_words:
                similarity = len(common_words) / len(query_words)
            else:
                similarity = 0.0

            scored_tickets.append(
                (ticket, similarity)
            )

        # Sort from most similar to least similar
        scored_tickets.sort(
            key=lambda x: x[1],
            reverse=True
        )

        results = []

        for ticket, similarity in scored_tickets[:top_k]:
            results.append(
                RetrievedTicket(
                    ticket_id=ticket["id"],
                    text=ticket["text"],
                    similarity=similarity,
                    resolution=ticket["resolution"],
                )
            )

        return results