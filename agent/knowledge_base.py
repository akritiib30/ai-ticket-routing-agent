import csv
from pathlib import Path
from datetime import datetime, timedelta


def load_seed_tickets():
    """
    Load historical support tickets for RAG retrieval.

    This now reads the same dataset (agent/data/tickets.csv) that
    train_model.py used to train the classifier, so retrieval,
    resolution suggestions, and classification all reason about the
    same categories and tickets instead of a small hardcoded sample.
    """

    csv_path = Path(__file__).parent / "data" / "tickets.csv"

    if not csv_path.exists():
        raise FileNotFoundError(
            f"Ticket dataset not found at: {csv_path}"
        )

    now = datetime.utcnow()
    tickets = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader, start=1):
            title = (row.get("title") or "").strip()
            description = (row.get("description") or "").strip()

            # Match the same text combination used to train the
            # classifier (title + " " + description) so retrieval
            # sees the ticket the same way the model was trained on.
            text = f"{title} {description}".strip()

            tickets.append({
                "id": f"T{i:04d}",
                "text": text,
                "category": (row.get("category") or "").strip(),
                "priority": (row.get("priority") or "").strip(),
                "resolution": (row.get("resolution") or "").strip(),
                # The dataset has no real timestamps. Spread synthetic
                # submission times over the last 30 days so any future
                # time-windowed recurring-issue logic has something
                # reasonable to work with.
                "submitted_at": now - timedelta(days=(i % 30)),
            })

    return tickets
