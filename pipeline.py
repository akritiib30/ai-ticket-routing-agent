"""Orchestrates the full ticket lifecycle:

Submission -> Preprocessing -> Classification -> Routing -> RAG Retrieval
-> Resolution Suggestion -> Confidence Check -> Decision -> Escalation
(matches the workflow stated in Section 3.2 of the design doc).

Each step is a separate module so any one of them (e.g. classification,
retrieval) can be swapped for a different implementation independently.
"""
from datetime import datetime

from . import preprocessing, routing, resolution, confidence as confidence_mod, escalation, recurring
from .classification import Classifier
from .retrieval import Retriever
from .knowledge_base import load_seed_tickets
from .models import Ticket, PipelineResult


class TicketAgentPipeline:
    def __init__(self):
        seed = load_seed_tickets()
        self.classifier = Classifier(seed)
        self.retriever = Retriever(seed)

    def run(self, ticket_id: str, raw_text: str, user: str = None) -> PipelineResult:
        ticket = Ticket(id=ticket_id, text=raw_text, submitted_at=datetime.utcnow(), user=user)

        clean_text = preprocessing.preprocess(raw_text)

        classification_result = self.classifier.predict(clean_text)
        routing_result = routing.route(classification_result.category)
        retrieved = self.retriever.search(clean_text, top_k=3)
        resolution_result = resolution.generate(clean_text, retrieved)
        confidence_result = confidence_mod.assess(classification_result, retrieved)
        recurring_flag = recurring.detect(retrieved)
        escalated = escalation.should_escalate(confidence_result)

        return PipelineResult(
            ticket=ticket,
            classification=classification_result,
            routing=routing_result,
            retrieved=retrieved,
            resolution=resolution_result,
            confidence=confidence_result,
            recurring=recurring_flag,
            escalated=escalated,
        )
