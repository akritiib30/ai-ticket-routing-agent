"""Orchestrates the full ticket lifecycle:

Submission -> Preprocessing -> Classification -> Routing -> RAG Retrieval
-> Resolution Suggestion -> Confidence Check -> Remediation
-> Decision -> Escalation.

Each step is a separate module so any one of them can be swapped
for a different implementation independently.
"""

from datetime import datetime

from . import (
    preprocessing,
    routing,
    resolution,
    confidence as confidence_mod,
    escalation,
    recurring,
    remediation,
)

from .classification import Classifier
from .retrieval import Retriever
from .knowledge_base import load_seed_tickets
from .models import Ticket, PipelineResult


class TicketAgentPipeline:

    def __init__(self):
        seed = load_seed_tickets()

        self.classifier = Classifier(seed)
        self.retriever = Retriever(seed)

    def run(
        self,
        ticket_id: str,
        raw_text: str,
        user: str = None
    ) -> PipelineResult:

        # 1. Create ticket
        ticket = Ticket(
            id=ticket_id,
            text=raw_text,
            submitted_at=datetime.utcnow(),
            user=user
        )

        # 2. Preprocess ticket text
        clean_text = preprocessing.preprocess(raw_text)

        # 3. Classify ticket
        classification_result = self.classifier.predict(clean_text)

        # 4. Route ticket to appropriate department
        routing_result = routing.route(
            classification_result.category
        )

        # 5. Retrieve similar historical tickets
        retrieved = self.retriever.search(
            clean_text,
            top_k=3
        )

        # 6. Generate resolution suggestion
        resolution_result = resolution.generate(
            clean_text,
            retrieved
        )

        # 7. Calculate confidence
        confidence_result = confidence_mod.assess(
            classification_result,
            retrieved
        )

        # 8. Attempt safe automated remediation
        remediation_result = remediation.diagnose_and_fix(
            classification_result.category,
            clean_text
        )

        # 9. Detect recurring issue
        recurring_flag = recurring.detect(
            retrieved
        )

        # 10. Decide whether human escalation is required
        escalated = escalation.should_escalate(
            confidence_result
        )

        # 11. Return complete pipeline result
        return PipelineResult(
            ticket=ticket,
            classification=classification_result,
            routing=routing_result,
            retrieved=retrieved,
            resolution=resolution_result,
            confidence=confidence_result,
            recurring=recurring_flag,
            escalated=escalated,
            remediation=remediation_result,
        )